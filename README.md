# 🔀 Unparallel

<!-- --8<-- [start:index] -->

<div align="center" markdown="1">

Create async HTTP requests with Python in no time.

[![Build status](https://github.com/RafaelWO/unparallel/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/RafaelWO/unparallel/actions?query=workflow%3Atest)
![Coverage Report](https://raw.githubusercontent.com/RafaelWO/unparallel/main/assets/images/coverage.svg)
<br>
[![Package Version](https://img.shields.io/pypi/v/unparallel.svg)](https://pypi.org/project/unparallel/)
[![Python Version](https://img.shields.io/pypi/pyversions/unparallel.svg)](https://pypi.org/project/unparallel/)
<br>
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/RafaelWO/unparallel/blob/main/.pre-commit-config.yaml)
[![License](https://img.shields.io/github/license/RafaelWO/unparallel)](https://github.com/RafaelWO/unparallel/blob/main/LICENSE)
<br>
[![Docs](https://img.shields.io/badge/docs-link-526cfe?style=for-the-badge)](https://rafaelwo.github.io/unparallel/)
[![Built with Material for MkDocs](https://img.shields.io/badge/Material_for_MkDocs-526CFE?style=for-the-badge&logo=MaterialForMkDocs&logoColor=white)](https://squidfunk.github.io/mkdocs-material/)

</div>

With Unparallel you can easily create thousands of web requests in an efficient way leveraging Python's async capabilities.

Unparallel is built on top of [HTTPX](https://github.com/encode/httpx/) and aims to support its rich set of features.

## Installation

```bash
pip install unparallel
```

## Example
A simple example of doing several GET requests to an HTTP web service:

```python
import asyncio

from unparallel import up


async def main():
    urls = [f"https://httpbin.org/get?i={i}" for i in range(5)]
    results = await up(urls)
    print([item["args"] for item in results])


if __name__ == "__main__":
    asyncio.run(main())
```

This prints:
```
Making async requests: 100%|███████████| 5/5 [00:00<00:00,  9.98it/s]
[{'i': '0'}, {'i': '1'}, {'i': '2'}, {'i': '3'}, {'i': '4'}]
```


Similarly, we can do a bunch of POST requests. This time we will use a single path but multiple payloads:

```python
import asyncio

from unparallel import up


async def main():
    url = "https://httpbin.org/post"
    payloads = [{"obj_id": i} for i in range(5)]
    results = await up(url, method="post", payloads=payloads)
    print([item["data"] for item in results])


asyncio.run(main())
```

This prints:
```
Making async requests: 100%|███████████| 5/5 [00:00<00:00,  9.98it/s]
['{"obj_id": 0}', '{"obj_id": 1}', '{"obj_id": 2}', '{"obj_id": 3}', '{"obj_id": 4}']
```

For more details on the usage and examples, check out the [docs][docs-usage].

## Why unparallel? Why async?
Async is a really powerful feature - especially when you have to wait for I/O.
When we create HTTP requests synchronously we have to wait for every response before we can start with the next request.
If we utilize asynchronous programming, our runtime thread can do other work (other requests) during those periods of waiting.

Here is an example of making 20 web requests synchronously vs. asynchronously via `unparallel`.

![Sync-vs-Async][sync-async-gif]

As you can see, the async version finishes in less than a second while the sync code runs for around 10 seconds.
The difference gets even more drastic if you create much more requests.

You can find the sync/async code in the [docs folder](https://github.com/RafaelWO/unparallel/blob/main/docs/sync_async/).

## Contributing
As this project is still in early development, I'm happy for any feedback and contributions!
Please refer to the [contributing guidelines][contrib] for details.

## License

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/RafaelWO/unparallel/blob/main/LICENSE) for more details.

## Credits
This project was heavily inspired by the blog post [Making 1 million requests with python-aiohttp](https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html) by Paweł Miech.

I created this project with [python-package-template](https://github.com/TezRomacH/python-package-template).

<!-- --8<-- [end:index] -->

[docs-usage]: https://rafaelwo.github.io/unparallel/usage/
[sync-async-gif]: https://raw.githubusercontent.com/RafaelWO/unparallel/main/docs/assets/sync-vs-async.gif
[contrib]: https://github.com/RafaelWO/unparallel/blob/main/CONTRIBUTING.md
