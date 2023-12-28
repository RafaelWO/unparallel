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

    Besides the exception itself, this contains the path, method, and (optional) payload
    of the failed request.
    """

    path: str
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
    path: str,
    method: str,
    json: Optional[Any] = None,
    max_retries_on_timeout: int = 3,
) -> Tuple[int, Any]:
    """Do a single web request for the given path, HTTP method, and playload.

    Args:
        idx (int): The index of the task (required for sorting afterwards).
        client (AsyncClient): The httpx client.
        path (str): The path after the base URI.
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
            response = await client.request(method, path, json=json)
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
            path=path,
            method=method,
            payload=json,
            exception=exception,
        ),
    )


async def request_urls(
    base_url: str,
    paths: Union[str, List[str]],
    method: str,
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    flatten_result: bool = False,
    max_retries_on_timeout: int = 3,
    limits: httpx.Limits = DEFAULT_LIMITS,
    timeouts: httpx.Timeout = DEFAULT_TIMEOUT,
    progress: bool = True,
) -> List[Any]:
    """
    Asynchronously issues requests to a URL at the specified path(s)
    via ``asyncio`` and ``httpx``.

    Args:
        base_url: The base URL of the service, e.g. http://localhost:8000.
        paths: One path or a list of paths, e.g. /foobar/. If one path but multiple
            payloads are supplied, that path is used for all requests.
        method: HTTP method to use, e.g. get, post, etc.
        headers: A dictionary of headers to use.
        payloads: A list of JSON payloads (dictionaries) for e.g. HTTP post requests.
            Used together with paths.
        flatten_result: If True and the response per request is a list, flatten that
            list of lists. This is useful when using paging.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.
        limits (httpx.Limits): The limits configuration for ``httpx``.
        timeouts (httpx.Timeout): The timeout configuration for ``httpx``.
        progress: If set to True, progress bar is shown

    Returns:
        A list of the response data per request in the same order as the input
        (paths/payloads).
    """
    tasks = []
    results = []

    logging.debug(
        f"Issuing {len(paths)} {method.upper()} request(s) to base URL '{base_url}' "
        f"with {limits.max_connections} max connections..."
    )
    async with httpx.AsyncClient(
        base_url=base_url, headers=headers, timeout=timeouts, limits=limits
    ) as client:
        for i, path in enumerate(paths):
            task = asyncio.create_task(
                single_request(
                    idx=i,
                    path=path,
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
    base_url: str,
    paths: Union[str, List[str]],
    method: str = "GET",
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
    """Creates async web requests to a URL at the specified path(s) via ``asyncio``
    and ``httpx``.

    Args:
        base_url (str):  The base URL of the target API/service.
        paths (Union[str, List[str]]): One path or a list of paths, e.g. /foobar/.
            If one path but multiple payloads are supplied, that path is used for all
            requests.
        method (str): HTTP method to use - one of ``GET``, ``OPTIONS``, ``HEAD``,
            ``POST``, ``PUT``, ``PATCH``, or ``DELETE``. Defaults to ``GET``.
        headers (Optional[Dict[str, Any]], optional): A dictionary of headers to use.
            Defaults to None.
        payloads (Optional[Any], optional): A list of JSON payloads (dictionaries) e.g.
            for HTTP post requests. Used together with paths. If one payload but
            multiple paths are supplied, that payload is used for all requests.
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
        ValueError: If the number of paths provided does not match the number of
            payloads (except if there is only one path).

    Returns:
        List[Any]:  A list of the response data per request in the same order as the
        input (paths/payloads).
    """
    # Check if method it valid
    if method.upper() not in VALID_HTTP_METHODS:
        raise ValueError(
            f"The method '{method}' is not a supported HTTP method. "
            f"Supported methods: {VALID_HTTP_METHODS}"
        )

    # Check if payloads align with paths
    if payloads:
        if isinstance(paths, str):
            paths = [paths]
        if not isinstance(payloads, list):
            payloads = [payloads]
        if len(paths) == 1 and len(payloads) > 1:
            logging.info(f"Using path '{paths[0]}' for all {len(payloads)} payloads")
            paths = paths * len(payloads)
        if len(payloads) == 1 and len(paths) > 1:
            logging.info(f"Using payload '{payloads[0]}' for all {len(paths)} paths")
            payloads = payloads * len(paths)
        if len(paths) != len(payloads):
            raise ValueError(
                f"The number of paths does not match the number of payloads: "
                f"{len(paths)} != {len(payloads)}"
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
        base_url=base_url,
        paths=paths,
        method=method,
        headers=headers,
        payloads=payloads,
        flatten_result=flatten_result,
        max_retries_on_timeout=max_retries_on_timeout,
        progress=progress,
        limits=limits,
        timeouts=timeouts,
    )
