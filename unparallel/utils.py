from types import TracebackType
from typing import Any, Type


class AsyncNullContext:
    """A nullcontext including __aenter__ and __aexit__ to support Python versions
    below 3.10."""

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(
        self, exc_type: Type[Exception], exc_value: Any, traceback: TracebackType
    ) -> None:
        pass
