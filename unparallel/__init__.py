"""Create async web requests in no time with `unparallel`"""

from importlib import metadata as importlib_metadata

from .unparallel import up


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()

__all__ = ["__version__", "up", "version"]
