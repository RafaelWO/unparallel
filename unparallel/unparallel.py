from typing import Any, Dict, List, Optional, Tuple, Union

import asyncio
import logging

from httpx import AsyncClient, Limits, TimeoutException
from tqdm.asyncio import tqdm as tqdm_async

logger = logging.getLogger(__name__)
VALID_HTTP_METHODS = ("get", "options", "head", "post", "put", "patch", "delete")


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
    client: AsyncClient,
    path: str,
    method: str,
    json: Optional[Any] = None,
    max_retries_on_timeout: int = 3,
) -> Tuple[int, Any]:
    """Do a single web request for the given path, HTTP method, and playload.

    Args:
        idx (int): The index of the task (required for sorting afterwards)
        client (AsyncClient): The httpx client
        path (str): The path after the base URI
        method (str): The HTTP method
        json (Optional[Any], optional): The JSON payload. Defaults to None.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.

    Returns:
        Tuple[int, Any]: A tuple of the index and the JSON response.
    """
    trial = 0
    exception = None
    method = method.lower()
    for trial in range(1, max_retries_on_timeout + 1):
        try:
            kwargs = {}
            if method in ["post", "put", "patch"]:
                kwargs["json"] = json
            response = await getattr(client, method.lower())(path, **kwargs)
            response.raise_for_status()
            json_data = response.json()
            return idx, json_data
        except TimeoutException as timeout_ex:
            exception = timeout_ex
            await asyncio.sleep(1)
        except Exception as ex:  # pylint: disable=broad-except
            exception = ex
            break

    logger.warning(
        f"{exception.__class__.__name__} was raised after {trial} tries: {exception}"
    )
    return idx, {
        "path": path,
        "method": method,
        "json": json,
        "exception": exception,
    }


async def request_urls(
    base_url: str,
    paths: Union[str, List[str]],
    method: str = "get",
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    flatten_result: bool = False,
    connection_limit: int = 100,
    max_retries_on_timeout: int = 3,
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
        connection_limit: The total number of simultaneous TCP connections
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.
        progress: If set to True, progress bar is shown

    Returns:
        A list of the response data per request in the same order as the input
        (paths/payloads).
    """
    tasks = []
    results = []

    limits = Limits(max_connections=connection_limit)
    async with AsyncClient(base_url=base_url, headers=headers, limits=limits) as client:
        for i, path in enumerate(paths):
            task = asyncio.create_task(
                single_request(
                    idx=i,
                    path=path,
                    client=client,
                    method=method,
                    json=payloads[i] if payloads else None,
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
    method: str = "get",
    headers: Optional[Dict[str, Any]] = None,
    payloads: Optional[Any] = None,
    flatten_result: bool = False,
    connection_limit: int = 100,
    max_retries_on_timeout: int = 3,
    progress: bool = True,
) -> List[Any]:
    """Creates async web requests to a URL at the specified path(s) via ``asyncio``
    and ``httpx``.

    Args:
        base_url (str):  The base URL of the target API/service.
        paths (Union[str, List[str]]): One path or a list of paths, e.g. /foobar/.
            If one path but multiple payloads are supplied, that path is used for all
            requests.
        method (str): HTTP method to use, e.g. get, post, etc.
            Defaults to "get".
        headers (Optional[Dict[str, Any]], optional): A dictionary of headers to use.
            Defaults to None.
        payloads (Optional[Any], optional): A list of JSON payloads (dictionaries) e.g.
            for HTTP post requests. Used together with paths. Defaults to None.
        flatten_result (bool): If True and the response per request is a list,
            flatten that list of lists. This is useful when using paging.
            Defaults to False.
        connection_limit (int): The total number of simultaneous TCP
            connections. Defaults to 100.
        max_retries_on_timeout (int): The maximum number retries if the requests fails
            due to a timeout (``httpx.TimeoutException``). Defauls to 3.
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
    if method not in VALID_HTTP_METHODS:
        raise ValueError(
            f"The method '{method}' is not a supported HTTP method. "
            f"Supported methods: {VALID_HTTP_METHODS}"
        )

    # Check if payloads align with paths
    if payloads:
        if isinstance(paths, str):
            paths = [paths]
        if len(paths) == 1 and len(payloads) > 1:
            logging.info(f"Using path '{paths[0]}' for all {len(payloads)} payloads")
            paths = paths * len(payloads)
        if len(paths) != len(payloads):
            raise ValueError(
                f"The number of paths does not match the number of payloads: "
                f"{len(paths)} != {len(payloads)}"
            )

    logging.debug(
        f"Issuing {len(paths)} {method.upper()} request(s) to base URL '{base_url}' "
        f"with {connection_limit} max connections..."
    )
    return await request_urls(
        base_url=base_url,
        paths=paths,
        method=method,
        headers=headers,
        payloads=payloads,
        flatten_result=flatten_result,
        connection_limit=connection_limit,
        max_retries_on_timeout=max_retries_on_timeout,
        progress=progress,
    )
