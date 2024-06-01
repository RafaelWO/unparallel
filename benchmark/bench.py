import asyncio
import datetime
import inspect
import itertools
import json
import time
from typing import Any
from unittest import mock

import httpx
from tqdm import tqdm

from unparallel import RequestError, up


async def single_request(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    semaphore: asyncio.Semaphore,
):
    """Do a single web request for the given URL, HTTP method, and playload."""
    try:
        async with semaphore:
            response = await client.request(method, url)
        return response
    # except (httpx.TimeoutException, httpx.NetworkError) as retry_ex:
    #     exception = retry_ex
    except asyncio.CancelledError as ex:
        return ex
    except Exception as ex:
        print(f"{ex.__class__.__name__} was raised: {ex}")
        return ex


async def print_status(tasks: list[asyncio.Task]):
    while True:
        locs = []
        for task in tasks:
            frame = task.get_stack(limit=1)[0]
            lineno = frame.f_lineno
            loc = (
                f"'{frame.f_code.co_filename}' line {lineno}: {frame.f_code.co_name}()"
            )
            code, offsest = inspect.getsourcelines(frame)
            loc += f"\n{code[lineno-offsest]}"
            locs.append(loc)

        for loc, group in itertools.groupby(sorted(locs)):
            for _cnt, _ in enumerate(group):
                pass
            print(f"{_cnt+1} tasks at {loc}")
        await asyncio.sleep(2)


async def request_urls(
    urls: list[str],
    method: str,
    base_url: str | None = None,
    limits: httpx.Limits | None = None,
    timeout: httpx.Timeout | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> list[Any]:
    tasks: list[asyncio.Task] = []
    results = []

    if semaphore is None:
        # Add a semaphore with a greater value than URLs
        semaphore = asyncio.Semaphore(len(urls) + 100)
        print("Created Semaphore with value:", semaphore._value)

    print("Creating requests...")
    async with httpx.AsyncClient(
        base_url=base_url or "", timeout=timeout, limits=limits
    ) as client:
        # monitor = asyncio.create_task(print_status(tasks))
        for url in urls:
            task = asyncio.create_task(
                single_request(
                    url=url,
                    client=client,
                    method=method,
                    semaphore=semaphore,
                )
            )
            tasks.append(task)

        print("Waiting for responses...")
        try:
            for task in asyncio.as_completed(tasks):
                res = await task
                results.append(res)

                print(f"\rProgress {len(results)}/{len(tasks)}", end="")
            print()
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
        # finally:
        #     monitor.cancel()
    return results


async def main():
    count = 1000
    base_url = "https://httpbin.org"
    urls = [f"/get?i={i}" for i in range(count)]

    limits = httpx.Limits(max_connections=100)
    # sem = Semaphore(100)
    responses = await request_urls(
        urls, method="GET", base_url=base_url, limits=limits, timeout=httpx.Timeout(10)
    )

    # Check if some requests failed
    valid_results = [item for item in responses if not isinstance(item, Exception)]
    fails = len(urls) - len(valid_results)
    print(f"{fails=} ({fails/len(urls):.2%})")


async def main_up():
    num_requests = [2000]  # [500, 1000, 1500, 2000]
    max_connections = list(range(100, 1001, 100)) + [None]
    semaphore_fact = [0.5, 0.8, 1]
    total_runs = len(num_requests) * len(max_connections) * len(semaphore_fact)

    base_url = "http://localhost:8000"
    results = []
    for nreqs, max_conns, sem_fact in tqdm(
        itertools.product(num_requests, max_connections, semaphore_fact),
        total=total_runs,
    ):
        urls = [f"/get?i={i}" for i in range(nreqs)]
        sem_value = 1000
        if max_conns:
            sem_value = max_conns * sem_fact

        print(f"{nreqs=}, {max_conns=}, {sem_fact=}, {sem_value=}")

        with mock.patch("unparallel.unparallel.SEMAPHORE_COUNT", sem_value):
            start_ts = time.time()
            responses = await up(
                urls,
                method="GET",
                base_url=base_url,
                max_connections=max_conns,
                progress=False,
            )
            took = time.time() - start_ts
            print(f"Took {took:.4f} seconds")

        # Check if some requests failed
        valid_results = [
            item for item in responses if not isinstance(item, RequestError)
        ]
        fails = len(responses) - len(valid_results)
        print(f"{fails=} ({fails/len(responses):.2%})")

        results.append(
            {
                "params": {
                    "num_requests": nreqs,
                    "max_connections": max_conns,
                    "semaphore_fact": sem_fact,
                    "semaphore_value": sem_value,
                },
                "took": took,
                "fails": fails,
            }
        )
        time.sleep(5)

    ts = datetime.datetime.now().isoformat()
    with open(f"bench_results_{ts}.json", "w") as file:
        json.dump(results, file, indent=2)


if __name__ == "__main__":
    asyncio.run(main_up())
