import pytest
from pytest_examples import CodeExample, EvalExample, find_examples


def skip_check(example: CodeExample):
    """Checks whether a code block is declared to be skipped via a comment above."""
    with open(example.path) as file:
        for i, line in enumerate(file):
            if i == example.start_line - 2:
                if line.strip() == "<!-- skip-test -->":
                    pytest.skip("Found 'skip-test' above source code")


@pytest.mark.parametrize("example", find_examples("README.md"), ids=str)
def test_readme(example: CodeExample, eval_example: EvalExample):
    skip_check(example)
    eval_example.lint(example)
    eval_example.run(example)


@pytest.mark.parametrize("example", find_examples("docs/usage.md"), ids=str)
def test_docs_usage(example: CodeExample, eval_example: EvalExample):
    find_examples("docs/examples/")
    skip_check(example)
    eval_example.lint(example)
    eval_example.run(example)
