# 🔀 Unparallel

<!-- --8<-- [start:index] -->

<div align="center" markdown="1">

Create Python async web requests in no time with **unparallel**!

[![Build status](https://github.com/RafaelWO/unparallel/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/RafaelWO/unparallel/actions?query=workflow%3Atest)
![Coverage Report](https://raw.githubusercontent.com/RafaelWO/unparallel/main/assets/images/coverage.svg)
[![Python Version](https://img.shields.io/pypi/pyversions/unparallel.svg)](https://pypi.org/project/unparallel/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/RafaelWO/unparallel/blob/main/.pre-commit-config.yaml)
[![License](https://img.shields.io/github/license/RafaelWO/unparallel)](https://github.com/RafaelWO/unparallel/blob/main/LICENSE)

</div>

## Installation

```bash
pip install unparallel
```

## Example
A simple example of doing a number of GET requests to an HTTP web service:

```python
import asyncio
from unparallel import up

async def main():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(5)]
    results = await up(url, paths)
    print([item["args"] for item in results])

asyncio.run(main())
```

This prints:
```
Making async requests: 100%|███████████| 5/5 [00:00<00:00,  9.98it/s]
[{'i': '0'}, {'i': '1'}, {'i': '2'}, {'i': '3'}, {'i': '4'}]
```

---

Similarly, we can do a bunch of POST requests. This time we will use a single path but multiple payloads:

```python
import asyncio
from unparallel import up

async def main():
    url = "https://httpbin.org"
    path = "/post"
    payloads = [{"obj_id": i} for i in range(5)]
    results = await up(url, path, method="post", payloads=payloads)
    print([item["data"] for item in results])

asyncio.run(main())
```

This prints:
```
Making async requests: 100%|███████████| 5/5 [00:00<00:00,  9.98it/s]
['{"obj_id": 0}', '{"obj_id": 1}', '{"obj_id": 2}', '{"obj_id": 3}', '{"obj_id": 4}']
```

<!-- --8<-- [end:index] -->

## Contributing
As this project is still in early development, I'm happy for any feedback and contributions! 
Please refer to the [contributing guidelines](./CONTRIBUTING.md) for details.

## License

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/RafaelWO/unparallel/blob/main/LICENSE) for more details.

## Credits 
I was heavily inspired for this project by the blog post [Making 1 million requests with python-aiohttp](https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html) by Paweł Miech.

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template).
