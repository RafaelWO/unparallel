import httpx
import pytest

from unparallel.unparallel import DEFAULT_LIMITS, DEFAULT_TIMEOUT
from unparallel.utils import (
    httpx_client,
    sort_by_idx,
)

BASE_URL = "http://test.com"


def test_order_by_idx():
    to_sort = [(4, "d"), (1, "a"), (3, "c"), (2, "b")]
    expected = list("abcd")
    assert sort_by_idx(to_sort) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client, headers",
    [
        (None, {"other": "client"}),
        (httpx.AsyncClient(headers={"my": "client"}), {"my": "client"}),
    ],
)
async def test_httpx_client(client, headers, respx_mock):
    route = respx_mock.get(BASE_URL, headers=headers)

    async with httpx_client(
        "", DEFAULT_LIMITS, DEFAULT_TIMEOUT, headers={"other": "client"}, client=client
    ) as client_:
        resp = await client_.get(BASE_URL)
        print(resp)

    route.calls.assert_called_once()
