import asyncio
import logging
from dataclasses import dataclass
from typing import (
    Any,
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


async def request_urls(
    urls: List[str],
    method: str,
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    response_fn: Optional[Callable[[httpx.Response], Any]] = DEFAULT_JSON_FN,
    flatten_result: bool = False,
    max_retries_on_timeout: int = 3,
    raise_for_status: bool = True,
    limits: httpx.Limits = DEFAULT_LIMITS,
    timeouts: httpx.Timeout = DEFAULT_TIMEOUT,
    client: Optional[httpx.AsyncClient] = None,
    progress: bool = True,
    semaphore_value: Optional[int] = None,
) -> List[Any]:
    """
    Asynchronously issues requests to the specified URL(s)
    via ``asyncio`` and ``httpx``.

    Args:
        urls (List[str]): A list of URLs for the HTTP requests.
        method (str): HTTP method to use, e.g. get, post, etc.
        base_url (Optional[str]): The base URL of the service, e.g. http://localhost:8000.
        headers (Optional[Dict[str, Any]]): A dictionary of headers to use.
        payloads (Optional[Any]): A list of JSON payloads (dictionaries) for e.g. HTTP
            post requests. Used together with ``urls``.
        response_fn (Optional[Callable[[httpx.Response], Any]]): The function to apply
            on every response of the HTTP requests. Defaults to ``httpx.Response.json``.
        flatten_result (bool): If True and the response per request is a list, flatten
            that list of lists. This is useful when using paging.
        raise_for_status (bool): If True, ``.raise_for_status()`` is called on every
            response.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defaults to ``3``.
        limits (httpx.Limits): The limits configuration for ``httpx``.
        timeouts (httpx.Timeout): The timeout configuration for ``httpx``.
        client (Optional[httpx.AsyncClient]): An instance of ``httpx.AsyncClient`` to be
            used for creating the HTTP requests.
        progress (bool): Whether to show a progress bar. Defaults to ``True``.
        semaphore_value: (Optional[int]): The value for the ``asyncio.Semaphore`` object
            that syncronizes the calls to HTTPX. Defaults to ``None``.

    Returns:
        A list of the response data per request in the same order as the input
        (URLs/payloads).
    """
    tasks = []
    results = []
    semaphore = asyncio.Semaphore(semaphore_value) if semaphore_value else None

    logging.debug(
        f"Issuing {len(urls)} {method.upper()} request(s) to base URL '{base_url}' "
        f"with {limits.max_connections} max connections..."
    )
    async with utils.httpx_client(
        base_url=base_url or "",
        headers=headers,
        timeouts=timeouts,
        limits=limits,
        client=client,
    ) as client:
        for i, url in enumerate(urls):
            task = asyncio.create_task(
                single_request(
                    idx=i,
                    url=url,
                    client=client,
                    method=method,
                    json=payloads[i] if payloads else None,
                    response_fn=response_fn,
                    max_retries_on_timeout=max_retries_on_timeout,
                    raise_for_status=raise_for_status,
                    semaphore=semaphore,
                )
            )
            tasks.append(task)

        for task in tqdm_async.as_completed(
            tasks, desc="Making async requests", disable=not progress
        ):
            res = await task
            results.append(res)

    results = utils.sort_by_idx(results)
    if flatten_result:
        return [
            item
            for sublist in results
            for item in ((sublist,) if isinstance(sublist, RequestError) else sublist)
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
    # Check if method it valid
    if method.upper() not in VALID_HTTP_METHODS:
        raise ValueError(
            f"The method '{method}' is not a supported HTTP method. "
            f"Supported methods: {VALID_HTTP_METHODS}"
        )

    # Wrap single URL into list to check for alignment with payload
    if isinstance(urls, str):
        urls = [urls]

    # Check if payloads align with URLs
    if payloads:
        if not isinstance(payloads, list):
            payloads = [payloads]
        if len(urls) == 1 and len(payloads) > 1:
            logging.info(f"Using URL '{urls[0]}' for all {len(payloads)} payloads")
            urls = urls * len(payloads)
        if len(payloads) == 1 and len(urls) > 1:
            logging.info(f"Using payload '{payloads[0]}' for all {len(urls)} URLs")
            payloads = payloads * len(urls)
        if len(urls) != len(payloads):
            raise ValueError(
                f"The number of URLs does not match the number of payloads: "
                f"{len(urls)} != {len(payloads)}"
            )

    if timeouts is None:
        timeouts = httpx.Timeout(timeout)
    if limits is None:
        if max_connections != DEFAULT_LIMITS.max_connections:
            limits = httpx.Limits(max_connections=max_connections)
            limits.max_keepalive_connections = DEFAULT_LIMITS.max_keepalive_connections
        else:
            limits = DEFAULT_LIMITS

    # After some benchmarking we discovered that syncronizing the HTTP requests with a
    # semaphore object that has the same value as the max_connections gives the best
    # performance.
    # Also, limiting the semaphore value to a maximum of 1k drastically reduced the
    # amount of timeouts.
    if isinstance(semaphore_value, UseMaxConnections):
        semaphore_value = min(
            max_connections or MAX_SEMAPHORE_COUNT, MAX_SEMAPHORE_COUNT
        )

    return await request_urls(
        urls=urls,
        method=method,
        base_url=base_url,
        headers=headers,
        payloads=payloads,
        response_fn=response_fn,
        flatten_result=flatten_result,
        max_retries_on_timeout=max_retries_on_timeout,
        raise_for_status=raise_for_status,
        limits=limits,
        timeouts=timeouts,
        client=client,
        progress=progress,
        semaphore_value=semaphore_value,
    )
