import asyncio
import logging
import warnings
from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import httpx
from tqdm.asyncio import tqdm as tqdm_async

from unparallel import utils

logger = logging.getLogger(__name__)

VALID_HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS")

DEFAULT_JSON_FN = httpx.Response.json
DEFAULT_TIMEOUT = httpx.Timeout(timeout=10)
DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

MAX_SEMAPHORE_COUNT = 1000


class UseMaxConnections:
    """
    For the parameter `semaphore` in the `up()` signature we need to be able to
    differentiate between the default "unset" state and `None`.

    The default value `semaphore=USE_MAX_CONNECTIONS` results in the value being the
    same as `max_connections`. However, the user can also set `semaphore` to some
    integer or `None`.
    """


USE_MAX_CONNECTIONS = UseMaxConnections()


@dataclass
class RequestError:
    """A dataclass wrapping an exception that was raised during a web request.

    Besides the exception itself, this contains the URL, method, and (optional) payload
    of the failed request.

    Attributes:
        url (str): The target URL of the request.
        method (str): The HTTP method.
        payload (Optional[Any]): The payload/body of the request.
        exception: (Exception): The exception that was raised.
    """

    url: str
    method: str
    payload: Optional[Any]
    exception: Exception


async def single_request(
    idx: int,
    client: httpx.AsyncClient,
    url: str,
    method: str,
    json: Optional[Any] = None,
    response_fn: Optional[Callable[[httpx.Response], Any]] = DEFAULT_JSON_FN,
    max_retries_on_timeout: int = 3,
    raise_for_status: bool = True,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> Tuple[int, Any]:
    """Do a single web request for the given URL, HTTP method, and playload.

    Args:
        idx (int): The index of the task (required for sorting afterwards).
        client (AsyncClient): The httpx client.
        url (str): The URL after the base URI.
        method (str): The HTTP method.
        json (Optional[Any], optional): The JSON payload. Defaults to ``None``.
        response_fn (Optional[Callable[[httpx.Response], Any]]): The function to apply
            on every response of the HTTP requests. Defaults to ``httpx.Response.json``.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defaults to ``3``.
        raise_for_status (bool): If True, ``.raise_for_status()`` is called on the
            response.
        semaphore (Optional[asyncio.Semaphore]): A semaphore object to synchronize
            the HTTP request. Defaults to ``None`` (-> nullcontext).

    Returns:
        Tuple[int, Any]: A tuple of the index and the JSON response.
    """
    trial = 0
    exception: Optional[Exception] = None
    for trial in range(max(0, max_retries_on_timeout) + 1):
        if trial > 0:
            await asyncio.sleep(1)

        try:
            async with semaphore or utils.AsyncNullContext():
                response = await client.request(method, url, json=json)
            if raise_for_status:
                response.raise_for_status()
            if response_fn is None:
                return idx, response
            result = response_fn(response)
            return idx, result
        except (httpx.TimeoutException, httpx.NetworkError) as retry_ex:
            exception = retry_ex
        except Exception as ex:  # pylint: disable=broad-except
            exception = ex
            break

    # this assert is here to make mypy happy
    assert exception is not None
    logger.warning(
        f"{exception.__class__.__name__} was raised after {trial+1} tries: {exception}"
    )
    return (
        idx,
        RequestError(
            url=url,
            method=method,
            payload=json,
            exception=exception,
        ),
    )


class Up:
    """A client to create async web requests to a set of URLs using ``asyncio``
    and ``httpx``.

    You can use the `Up` client to create web requests and asyncrounously loop over
    the results:

    ```python
    import asyncio
    from unparallel import Up

    async def main():
        urls = [f"https://httpbin.org/get?i={i}" for i in range(5)]
        async for result in Up(urls, method="GET"):
            print(result["args"])

    asyncio.run(main())
    #> [{'i': '0'}, {'i': '2'}, {'i': '1'}, {'i': '4'}, {'i': '3'}]
    ```

    If you do something with the result right away, the above is very memory
    efficient. Note that the results are **not** in the same order as the input.

    If you care about the order (and don't care about having all responses in
    memory), you can use `.all()` on the `Up` client:

    ```python
    import asyncio
    from unparallel import Up

    async def main():
        urls = [f"https://httpbin.org/get?i={i}" for i in range(5)]
        results = await Up(urls, method="GET").all()
        print([item["args"] for item in results])

    asyncio.run(main())
    #> [{'i': '0'}, {'i': '2'}, {'i': '1'}, {'i': '3'}, {'i': '4'}]
    ```

    Now the results are sorted in the same way as the input order.
    """

    def __init__(
        self,
        urls: Union[str, List[str]],
        method: str = "GET",
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        payloads: Optional[Any] = None,
        response_fn: Optional[Callable[[httpx.Response], Any]] = DEFAULT_JSON_FN,
        flatten_result: bool = False,
        max_connections: Optional[int] = 100,
        timeout: Optional[int] = 10,
        max_retries_on_timeout: int = 3,
        raise_for_status: bool = True,
        limits: Optional[httpx.Limits] = None,
        timeouts: Optional[httpx.Timeout] = None,
        client: Optional[httpx.AsyncClient] = None,
        progress: bool = True,
        semaphore_value: Union[int, UseMaxConnections, None] = USE_MAX_CONNECTIONS,
    ) -> None:
        # Check if method it valid
        if method.upper() not in VALID_HTTP_METHODS:
            raise ValueError(
                f"The method '{method}' is not a supported HTTP method. "
                f"Supported methods: {VALID_HTTP_METHODS}"
            )
        self.method = method

        # Wrap single URL into list to check for alignment with payload
        if isinstance(urls, str):
            self.urls = [urls]
        else:
            self.urls = urls

        # Check if payloads align with URLs
        self.payloads: Optional[List[Any]] = None
        if payloads:
            if not isinstance(payloads, list):
                self.payloads = [payloads]
            else:
                self.payloads = payloads

            if len(self.urls) == 1 and len(self.payloads) > 1:
                logging.info(
                    f"Using URL '{self.urls[0]}' for all {len(self.payloads)} payloads"
                )
                self.urls = self.urls * len(self.payloads)
            if len(self.payloads) == 1 and len(self.urls) > 1:
                logging.info(
                    f"Using payload '{self.payloads[0]}' for all {len(self.urls)} URLs"
                )
                self.payloads = self.payloads * len(self.urls)
            if len(self.urls) != len(self.payloads):
                raise ValueError(
                    f"The number of URLs does not match the number of payloads: "
                    f"{len(self.urls)} != {len(self.payloads)}"
                )

        if timeouts is None:
            self.timeouts = httpx.Timeout(timeout)
        else:
            self.timeouts = timeouts

        if limits is None:
            if max_connections != DEFAULT_LIMITS.max_connections:
                self.limits = httpx.Limits(max_connections=max_connections)
                self.limits.max_keepalive_connections = (
                    DEFAULT_LIMITS.max_keepalive_connections
                )
            else:
                self.limits = DEFAULT_LIMITS
        else:
            self.limits = limits

        # After some benchmarking we discovered that syncronizing the HTTP requests with
        # a semaphore object that has the same value as the max_connections gives the
        # best performance.
        # Also, limiting the semaphore value to a maximum of 1k drastically reduced the
        # amount of timeouts.
        self.semaphore_value: Optional[int]
        if isinstance(semaphore_value, UseMaxConnections):
            self.semaphore_value = min(
                max_connections or MAX_SEMAPHORE_COUNT, MAX_SEMAPHORE_COUNT
            )
        else:
            self.semaphore_value = semaphore_value

        self.base_url = base_url
        self.headers = headers
        self.response_fn = response_fn
        self.flatten_result = flatten_result
        self.max_retries_on_timeout = max_retries_on_timeout
        self.raise_for_status = raise_for_status
        self.client = client
        self.progress = progress

    async def _request_urls(self) -> AsyncIterator[Tuple[int, Any]]:
        """Creates web requests with ``httpx`` as ``asyncio`` tasks.

        Returns:
            AsyncIterator[Tuple[int, Any]]: An async iterator yielding one
            response/result of a request at a time.

        Yields:
            Tuple[int, Any]: A results of a web request as a tuple of index (the
            position in the input) and the actual result.
        """
        # tasks = []
        semaphore = (
            asyncio.Semaphore(self.semaphore_value) if self.semaphore_value else None
        )

        logging.debug(
            f"Issuing {len(self.urls)} {self.method.upper()} request(s) to base URL "
            f"'{self.base_url}' with {self.limits.max_connections} max connections..."
        )
        async with utils.httpx_client(
            base_url=self.base_url or "",
            headers=self.headers,
            timeouts=self.timeouts,
            limits=self.limits,
            client=self.client,
        ) as client:
            task_gen = (
                asyncio.create_task(
                    single_request(
                        idx=i,
                        url=url,
                        client=client,
                        method=self.method,
                        json=self.payloads[i] if self.payloads else None,
                        response_fn=self.response_fn,
                        max_retries_on_timeout=self.max_retries_on_timeout,
                        raise_for_status=self.raise_for_status,
                        semaphore=semaphore,
                    )
                )
                for i, url in enumerate(self.urls)
            )

            for task in tqdm_async.as_completed(
                task_gen,
                desc="Making async requests",
                disable=not self.progress,
                total=len(self.urls),
            ):
                yield await task

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Creates web requests with ``httpx`` as ``asyncio`` tasks.

        Returns:
            AsyncIterator[Any]: An async iterator yielding one response/result of a
            web request at a time.

        Yields:
            Iterator[AsyncIterator[Any]]: The response/result of a web request.
        """
        if self.flatten_result:
            warnings.warn(
                "Setting `flatten_result=True` has no effect when iterating over the "
                "results.",
                stacklevel=2,
            )

        async for result in self._request_urls():
            yield result[1]

    async def all(self) -> List[Any]:
        """Asynchronously issues requests to the specified URL(s) and collects all the
        responses. The output is sorted based on the order of the input and can be
        flattened as well if `flatten_result` is set to `True`.

        Returns:
            List[Any]: A list of the response data per request in the same order as the
            input (URLs/payloads).
        """
        results = []

        async for result in self._request_urls():
            results.append(result)

        results = utils.sort_by_idx(results)
        if self.flatten_result:
            return [
                item
                for sublist in results
                for item in (
                    (sublist,) if isinstance(sublist, RequestError) else sublist
                )
            ]
        return results


async def up(
    urls: Union[str, List[str]],
    method: str = "GET",
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    response_fn: Optional[Callable[[httpx.Response], Any]] = DEFAULT_JSON_FN,
    flatten_result: bool = False,
    max_connections: Optional[int] = 100,
    timeout: Optional[int] = 10,
    max_retries_on_timeout: int = 3,
    raise_for_status: bool = True,
    limits: Optional[httpx.Limits] = None,
    timeouts: Optional[httpx.Timeout] = None,
    client: Optional[httpx.AsyncClient] = None,
    progress: bool = True,
    semaphore_value: Union[int, UseMaxConnections, None] = USE_MAX_CONNECTIONS,
) -> List[Any]:
    """Creates async web requests to the specified URL(s) using ``asyncio``
    and ``httpx``.

    Args:
        urls (Union[str, List[str]]): A list of URLs as the targets for the requests.
            If only one URL but multiple payloads are supplied, that URL is used for
            all requests.
            If a ``base_url`` is supplied, this can also be a list of paths
            (or one path).
        method (str): HTTP method to use - one of ``GET``, ``OPTIONS``, ``HEAD``,
            ``POST``, ``PUT``, ``PATCH``, or ``DELETE``. Defaults to ``GET``.
        base_url (Optional[str]):  The base URL of the target API/service. Defaults to
            ``None``.
        headers (Optional[Dict[str, Any]], optional): A dictionary of headers to use.
            Defaults to ``None``.
        payloads (Optional[Any], optional): A list of JSON payloads (dictionaries) e.g.
            for HTTP post requests. Used together with ``urls``. If one payload but
            multiple URLs are supplied, that payload is used for all requests.
            Defaults to ``None``.
        response_fn (Optional[Callable[[httpx.Response], Any]]): The function (callback)
            to apply on every response of the HTTP requests. This can be an existing
            function of ``httpx.Response`` like ``.json()`` or ``.read()``, or a custom
            function which takes the ``httpx.Response`` as the argument returns ``Any``.
            If you set this to ``None``, you will get the raw ``httpx.Response``.
            Defaults to ``httpx.Response.json``.
        flatten_result (bool): If True and the response per request is a list,
            flatten that list of lists. This is useful when using paging.
            Defaults to ``False``.
        max_connections (int): The total number of simultaneous TCP
            connections. Defaults to ``100``. This is passed into ``httpx.Limits``.
        timeout (int): The timeout for requests in seconds. Defaults to 10.
            This is passed into ``httpx.Timeout``.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defaults to ``3``.
        raise_for_status (bool): If True, ``.raise_for_status()`` is called on overy
            response.
        limits (Optional[httpx.Limits]): The limits configuration for ``httpx``.
            If specified, this overrides the ``max_connections`` parameter.
        timeouts (Optional[httpx.Timeout]): The timeout configuration for ``httpx``.
            If specified, this overrides the ``timeout`` parameter.
        client (Optional[httpx.AsyncClient]): An instance of ``httpx.AsyncClient`` to be
            used for creating the HTTP requests. **Note that if you pass a client, all
            other options that parametrize the client (``base_url``, ``headers``,
            ``limits``, and ``timeouts``) are ignored**. Defaults to ``None``.
        progress (bool): If set to ``True``, progress bar is shown.
            Defaults to ``True``.
        semaphore_value: (Union[int, UseMaxConnections, None]): The value for the
            ``asyncio.Semaphore`` object that syncronizes the calls to HTTPX. Defaults
            to the number of ``max_connections``.

    Raises:
        ValueError: If the HTTP method is not valid.
        ValueError: If the number of URLs provided does not match the number of
            payloads (except if there is only one URL).

    Returns:
        List[Any]:  A list of the response data per request in the same order as the
        input (URLs/payloads).
    """
    up_obj = Up(
        urls=urls,
        method=method,
        base_url=base_url,
        headers=headers,
        payloads=payloads,
        response_fn=response_fn,
        flatten_result=flatten_result,
        max_connections=max_connections,
        timeout=timeout,
        max_retries_on_timeout=max_retries_on_timeout,
        raise_for_status=raise_for_status,
        limits=limits,
        timeouts=timeouts,
        client=client,
        progress=progress,
        semaphore_value=semaphore_value,
    )

    return await up_obj.all()
