import asyncio

from unparallel import up


async def main():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(20)]

    results = await up(url, paths)

    assert len(results) == 20


if __name__ == "__main__":
    asyncio.run(main())
