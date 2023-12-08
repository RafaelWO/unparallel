# 🔀 Unparallel

<div align="center">

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

## Contributing
As this project is still in early development, I'm happy for any feedback and contributions! 
Please refer to the [contributing guidelines](./CONTRIBUTING.md) for details.

## Makefile usage

[`Makefile`](https://github.com/RafaelWO/unparallel/blob/main/Makefile) contains a lot of functions for faster development.

<details>
<summary>1. Download and remove Poetry</summary>
<p>

To download and install Poetry run:

```bash
make poetry-download
```

To uninstall

```bash
make poetry-remove
```

</p>
</details>

<details>
<summary>2. Install all dependencies and pre-commit hooks</summary>
<p>

Install requirements:

```bash
make install
```

Pre-commit hooks coulb be installed after `git init` via

```bash
make pre-commit-install
```

</p>
</details>

<details>
<summary>3. Codestyle</summary>
<p>

Automatic formatting uses `pyupgrade`, `isort` and `black`.

```bash
make codestyle

# or use synonym
make formatting
```

Codestyle checks only, without rewriting files:

```bash
make check-codestyle
```

> Note: `check-codestyle` uses `isort` and `black` library

<details>
<summary>4. Code security</summary>
<p>

```bash
make check-safety
```

This command launches `Poetry` integrity checks as well as identifies security issues with `Safety` and `Bandit`.

```bash
make check-safety
```

</p>
</details>

</p>
</details>

<details>
<summary>5. Type checks</summary>
<p>

Run `mypy` static type checker

```bash
make check-typing
```

</p>
</details>

<details>
<summary>6. Tests with coverage badges</summary>
<p>

Run `pytest`

```bash
make test
```

</p>
</details>

<details>
<summary>7. All linters</summary>
<p>

Of course there is a command to run all linters in one:

```bash
make lint
```

the same as:

```bash
make check-codestyle && make check-typing
```

</p>
</details>

<details>
<summary>8. Docker</summary>
<p>

```bash
make docker-build
```

which is equivalent to:

```bash
make docker-build VERSION=latest
```

Remove docker image with

```bash
make docker-remove
```

More information [about docker](https://github.com/RafaelWO/unparallel/tree/main/docker).

</p>
</details>

<details>
<summary>9. Cleanup</summary>
<p>
Delete pycache files

```bash
make pycache-remove
```

Remove package build

```bash
make build-remove
```

Delete .DS_STORE files

```bash
make dsstore-remove
```

Remove .mypycache

```bash
make mypycache-remove
```

Or to remove all above run:

```bash
make cleanup
```

</p>
</details>

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/RafaelWO/unparallel/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |       🚀 Features       |
| `bug`, `refactoring`, `bugfix`, `fix` | 🔧 Fixes & Refactoring  |
|       `build`, `ci`, `testing`        | 📦 Build System & CI/CD |
|              `breaking`               |   💥 Breaking Changes   |
|            `documentation`            |    📝 Documentation     |
|            `dependencies`             | ⬆️ Dependencies updates |

You can update it in [`release-drafter.yml`](https://github.com/RafaelWO/unparallel/blob/main/.github/release-drafter.yml).

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you. Dependabot creates the `dependencies` label. Create the remaining labels on the Issues tab of your GitHub repository, when you need them.

## 🛡 License

[![License](https://img.shields.io/github/license/RafaelWO/unparallel)](https://github.com/RafaelWO/unparallel/blob/main/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/RafaelWO/unparallel/blob/main/LICENSE) for more details.

## Credits 
I was heavily inspired for this project by the blog post [Making 1 million requests with python-aiohttp](https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html) by Paweł Miech.

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template).
