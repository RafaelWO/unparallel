from typing import List, Union

import asyncio
import logging

from httpx import AsyncClient, Limits
from tqdm.asyncio import tqdm as tqdm_async

logger = logging.getLogger(__name__)
MAX_TRIALS = 3


def order_by_idx(results):
    return [item[1] for item in sorted(results, key=lambda x: x[0])]


async def single_request(
    idx: int, client: AsyncClient, path: str, method: str, json=None
):
    trial = 0
    exception = None
    method = method.lower()
    for trial in range(1, MAX_TRIALS + 1):
        try:
            kwargs = {}
            if method in ["post", "put", "patch"]:
                kwargs["json"] = json
            response = await getattr(client, method.lower())(path, **kwargs)
            response.raise_for_status()
            json_data = response.json()
            return idx, json_data
        except Exception as ex:  # pylint: disable=broad-except
            exception = ex
            await asyncio.sleep(1)

    ex_dict = getattr(exception, "__dict__", {})
    logger.warning(
        f"{exception.__class__.__name__} was raised after {trial} tries: {ex_dict}"
    )
    return idx, {
        "path": path,
        "method": method,
        "json": json,
        "exception": str(ex_dict),
    }


async def request_urls(
    base_url: str,
    paths: Union[str, List[str]],
    method: str,
    headers: dict = None,
    payloads: list = None,
    flatten_result=False,
    connection_limit=100,
    progress=True,
):
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
            list of lists.
        connection_limit: The total number of simultaneous aiohttp TCP connections
        progress: If set to True, progress bar is shown

    Returns:
        A list of the response data per request in the same order as the input
        (paths/payloads).

    Raises:
        ValueError: If the number of paths provided does not match the number of
            payloads (except if there is only one path).
    """
    tasks = []
    results = []

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

        for task in tqdm_async.as_completed(tasks, disable=not progress):
            res = await task
            results.append(res)

    results = order_by_idx(results)
    if flatten_result:
        return [item for sublist in results for item in sublist]
    return results
