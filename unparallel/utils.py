class AsyncNullContext:
    """A nullcontext including __aenter__ and __aexit__ to support Python versions
    below 3.10."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, *excinfo):
        pass
