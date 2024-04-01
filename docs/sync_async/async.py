import asyncio

from unparallel import up

NUM_REQUESTS = 20


async def main():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(NUM_REQUESTS)]

    results = await up(paths, base_url=url)

    assert len(results) == NUM_REQUESTS


if __name__ == "__main__":
    asyncio.run(main())
