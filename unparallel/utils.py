from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, Optional

import httpx


class AsyncNullContext:
    """A nullcontext including __aenter__ and __aexit__ to support Python versions
    below 3.10."""

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(
        self, exc_type: type[Exception], exc_value: Any, traceback: TracebackType
    ) -> None:
        pass


@asynccontextmanager
async def httpx_client(
    base_url: str,
    limits: httpx.Limits,
    timeouts: httpx.Timeout,
    headers: Optional[dict[str, Any]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> AsyncIterator[httpx.AsyncClient]:
    if client is not None:
        yield client
    else:
        async with httpx.AsyncClient(
            base_url=base_url or "", headers=headers, timeout=timeouts, limits=limits
        ) as client:
            yield client


def sort_by_idx(results: list[tuple[int, Any]]) -> list[Any]:
    """Sorts a list of tuples (index, value) by the index and return just the values.

    Args:
        results (List[Tuple[int, Any]]): A list of tuples (index, value) to be sorted.

    Returns:
        List[Any]: The values as a list.
    """
    return [item[1] for item in sorted(results, key=lambda x: x[0])]
