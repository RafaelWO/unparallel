import re

import pytest
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


@pytest.mark.parametrize("example", find_examples("README.md"), ids=str)
def test_readme(example: CodeExample, eval_example: EvalExample):
    check_for_skip(example)
    limit_requests(example)
    eval_example.lint(example)
    eval_example.run(example)


@pytest.mark.parametrize("example", find_examples("docs/usage.md"), ids=str)
def test_docs_usage(example: CodeExample, eval_example: EvalExample):
    check_for_skip(example)
    limit_requests(example)
    eval_example.lint(example)
    eval_example.run(example)
