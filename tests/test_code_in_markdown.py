import functools
import re
import urllib.parse

import httpx
import pytest
import respx
from httpx import Response
from pytest_examples import CodeExample, EvalExample, find_examples


def check_for_skip(example: CodeExample):
    """Checks whether a code block is declared to be skipped via a comment above."""
    with open(example.path) as file:
        for i, line in enumerate(file):
            if i == example.start_line - 2:
                if line.strip() == "<!-- skip-test -->":
                    pytest.skip("Found 'skip-test' above source code")


def limit_requests(example: CodeExample, num_requests: int = 3):
    """Change the example's source code to only make `num_requests` requests."""
    example.source = re.sub(
        r"range\([\d, ]+\)", f"range({num_requests})", example.source
    )


def mock_urls(example: CodeExample):
    """Finds URLs in code examples and mocks them so that the tests don't rely on the
    live-service.
    """
    for url in re.findall(r"\"http.+?\"", example.source):
        url = url.strip('"')
        host = urllib.parse.urlsplit(url).hostname

        def my_side_effect(
            request: httpx.Request,
            url,
        ):
            response = "mocked"
            if "httpbin" in url:
                response = {
                    "args": urllib.parse.parse_qs(request.url.query.decode()),
                    "data": {"foo": "bar"},
                    "headers": {
                        "Accept": "application/json",
                        "Authorization": "Basic qpowe3jioqoni2q1",
                    },
                }
            elif "universities.hipolabs" in url:
                response = [{"page": 1}, {"page": 2}]
            else:
                response = "mocked"
            return Response(200, json=response)

        side_effect = functools.partial(my_side_effect, url=url)
        route = respx.route(host=host, method__in=["GET", "POST", "HEAD"])
        route.side_effect = side_effect


@respx.mock
@pytest.mark.parametrize("example", find_examples("README.md"), ids=str)
def test_readme(example: CodeExample, eval_example: EvalExample):
    check_for_skip(example)
    mock_urls(example)

    eval_example.set_config(line_length=80)
    eval_example.lint(example)

    eval_example.run(example)


@respx.mock
@pytest.mark.parametrize("example", find_examples("docs/usage.md"), ids=str)
def test_docs_usage(example: CodeExample, eval_example: EvalExample):
    check_for_skip(example)
    mock_urls(example)

    eval_example.set_config(line_length=80)
    eval_example.lint(example)

    eval_example.run(example)


@pytest.mark.parametrize("example", find_examples("unparallel/unparallel.py"), ids=str)
def test_docstrings(example: CodeExample, eval_example: EvalExample):
    eval_example.run(example)
