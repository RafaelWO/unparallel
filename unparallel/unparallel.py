import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from tqdm.asyncio import tqdm as tqdm_async

logger = logging.getLogger(__name__)
VALID_HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS")

DEFAULT_TIMEOUT = httpx.Timeout(timeout=10)
DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)


@dataclass
class RequestError:
    """A dataclass wrapping an exception that was raised during a web request.

    Besides the exception itself, this contains the URL, method, and (optional) payload
    of the failed request.
    """

    url: str
    method: str
    payload: Optional[Any]
    exception: Exception


def sort_by_idx(results: List[Tuple[int, Any]]) -> List[Any]:
    """Sorts a list of tuples (index, value) by the index and return just the values.

    Args:
        results (List[Tuple[int, Any]]): A list of tuples (index, value) to be sorted.

    Returns:
        List[Any]: The values as a list.
    """
    return [item[1] for item in sorted(results, key=lambda x: x[0])]


async def single_request(
    idx: int,
    client: httpx.AsyncClient,
    url: str,
    method: str,
    json: Optional[Any] = None,
    max_retries_on_timeout: int = 3,
) -> Tuple[int, Any]:
    """Do a single web request for the given URL, HTTP method, and playload.

    Args:
        idx (int): The index of the task (required for sorting afterwards).
        client (AsyncClient): The httpx client.
        url (str): The URL after the base URI.
        method (str): The HTTP method.
        json (Optional[Any], optional): The JSON payload. Defaults to None.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.

    Returns:
        Tuple[int, Any]: A tuple of the index and the JSON response.
    """
    trial = 0
    exception: Optional[Exception] = None
    for trial in range(1, max_retries_on_timeout + 1):
        try:
            response = await client.request(method, url, json=json)
            response.raise_for_status()
            json_data = response.json()
            return idx, json_data
        except httpx.TimeoutException as timeout_ex:
            exception = timeout_ex
            await asyncio.sleep(1)
        except Exception as ex:  # pylint: disable=broad-except
            exception = ex
            break

    # this assert is here to make mypy happy
    assert exception is not None
    logger.warning(
        f"{exception.__class__.__name__} was raised after {trial} tries: {exception}"
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
    base_url: str,
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    flatten_result: bool = False,
    max_retries_on_timeout: int = 3,
    limits: httpx.Limits = DEFAULT_LIMITS,
    timeouts: httpx.Timeout = DEFAULT_TIMEOUT,
    progress: bool = True,
) -> List[Any]:
    """
    Asynchronously issues requests to the specified URL(s)
    via ``asyncio`` and ``httpx``.

    Args:
        urls: A list of URLs for the HTTP requests.
        method: HTTP method to use, e.g. get, post, etc.
        base_url: The base URL of the service, e.g. http://localhost:8000.
        headers: A dictionary of headers to use.
        payloads: A list of JSON payloads (dictionaries) for e.g. HTTP post requests.
            Used together with ``urls``.
        flatten_result: If True and the response per request is a list, flatten that
            list of lists. This is useful when using paging.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.
        limits (httpx.Limits): The limits configuration for ``httpx``.
        timeouts (httpx.Timeout): The timeout configuration for ``httpx``.
        progress: If set to True, progress bar is shown

    Returns:
        A list of the response data per request in the same order as the input
        (URLs/payloads).
    """
    tasks = []
    results = []

    logging.debug(
        f"Issuing {len(urls)} {method.upper()} request(s) to base URL '{base_url}' "
        f"with {limits.max_connections} max connections..."
    )
    async with httpx.AsyncClient(
        base_url=base_url or "", headers=headers, timeout=timeouts, limits=limits
    ) as client:
        for i, url in enumerate(urls):
            task = asyncio.create_task(
                single_request(
                    idx=i,
                    url=url,
                    client=client,
                    method=method,
                    json=payloads[i] if payloads else None,
                    max_retries_on_timeout=max_retries_on_timeout,
                )
            )
            tasks.append(task)

        for task in tqdm_async.as_completed(
            tasks, desc="Making async requests", disable=not progress
        ):
            res = await task
            results.append(res)

    results = sort_by_idx(results)
    if flatten_result:
        return [item for sublist in results for item in sublist]
    return results


async def up(
    urls: Union[str, List[str]],
    method: str = "GET",
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    flatten_result: bool = False,
    max_connections: Optional[int] = 100,
    timeout: Optional[int] = 10,
    max_retries_on_timeout: int = 3,
    limits: Optional[httpx.Limits] = None,
    timeouts: Optional[httpx.Timeout] = None,
    progress: bool = True,
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
            None.
        headers (Optional[Dict[str, Any]], optional): A dictionary of headers to use.
            Defaults to None.
        payloads (Optional[Any], optional): A list of JSON payloads (dictionaries) e.g.
            for HTTP post requests. Used together with ``urls``. If one payload but
            multiple URLs are supplied, that payload is used for all requests.
            Defaults to None.
        flatten_result (bool): If True and the response per request is a list,
            flatten that list of lists. This is useful when using paging.
            Defaults to False.
        max_connections (int): The total number of simultaneous TCP
            connections. Defaults to 100. This is passed into ``httpx.Limits``.
        timeout (int): The timeout for requests in seconds. Defaults to 10.
            This is passed into ``httpx.Timeout``.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.
        limits (Optional[httpx.Limits]): The limits configuration for ``httpx``.
            If specified, this overrides the ``max_connections`` parameter.
        timeouts (Optional[httpx.Timeout]): The timeout configuration for ``httpx``.
            If specified, this overrides the ``timeout`` parameter.
        progress (bool): If set to True, progress bar is shown.
            Defaults to True.

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

    # Check if payloads align with URLs
    if payloads:
        if isinstance(urls, str):
            urls = [urls]
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

    return await request_urls(
        urls=urls,
        method=method,
        base_url=base_url,
        headers=headers,
        payloads=payloads,
        flatten_result=flatten_result,
        max_retries_on_timeout=max_retries_on_timeout,
        progress=progress,
        limits=limits,
        timeouts=timeouts,
    )
