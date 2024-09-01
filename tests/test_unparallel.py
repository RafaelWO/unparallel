import asyncio
from unittest import mock

import pytest
from httpx import AsyncClient, Response, TimeoutException

from unparallel import Up
from unparallel.unparallel import (
    RequestError,
    single_request,
)

BASE_URL = "http://test.com"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, method, payload",
    [
        (BASE_URL, "get", "data"),
        (f"{BASE_URL}/foo", "post", "data"),
    ],
)
async def test_single_request(url, method, payload, respx_mock):
    respx_mock.request(method, url).mock(return_value=Response(200, json=payload))
    session = AsyncClient()
    result = await single_request(1, session, url=url, method=method)
    assert result == (1, payload)
    await session.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, return_value, response_fn, expected",
    [
        ("HEAD", Response(200), lambda x: x.status_code, 200),
        ("GET", Response(200, text="foobar"), lambda x: x.text, "foobar"),
        ("POST", Response(200), None, Response(200)),
    ],
    ids=["HEAD_status", "GET_text", "POST_raw"],
)
async def test_single_request_custom_response(
    respx_mock, method, return_value, response_fn, expected
):
    respx_mock.request(method, BASE_URL).mock(return_value=return_value)

    async with AsyncClient() as session:
        _, result = await single_request(
            1, session, BASE_URL, method=method, response_fn=response_fn
        )

    if isinstance(expected, Response):
        assert isinstance(result, Response)
        assert result.status_code == expected.status_code
    else:
        assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, do_raise", [(500, True), (500, False), (404, True), (404, False)]
)
async def test_single_request_fail(status, do_raise, respx_mock):
    url = f"{BASE_URL}/foo"
    respx_mock.get(url).mock(return_value=Response(status))
    session = AsyncClient()
    idx, result = await single_request(
        1, session, url=url, method="GET", raise_for_status=do_raise, response_fn=None
    )

    assert idx == 1

    if do_raise:
        assert isinstance(result, RequestError)
        assert result.method == "GET"
        assert result.url == url
        assert isinstance(result.exception, Exception)
    else:
        assert isinstance(result, Response)

    await session.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("retries", [0, 1, 3])
async def test_single_request_timeout(respx_mock, retries: int):
    url = f"{BASE_URL}/foo"
    route = respx_mock.get(url).mock(side_effect=TimeoutException)
    session = AsyncClient()
    with mock.patch("asyncio.sleep", wraps=asyncio.sleep) as mocked_sleep:
        result = await single_request(
            1, session, url=url, method="GET", max_retries_on_timeout=retries
        )
        assert isinstance(result[1], RequestError)
        assert route.call_count == retries + 1
        assert mocked_sleep.call_count == retries
    await session.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "flatten, expected",
    [(False, [[1, 2, 3], [4, 5, 6]]), (True, [1, 2, 3, 4, 5, 6])],
    ids=["not-flat", "flat"],
)
@mock.patch(
    "unparallel.unparallel.single_request", side_effect=[(1, [1, 2, 3]), (2, [4, 5, 6])]
)
async def test_request_urls_flat(_patched_fetch, flatten, expected):
    up_obj = Up(
        urls=["/a", "/b"], method="get", base_url=BASE_URL, flatten_result=flatten
    )
    results = await up_obj.all()
    assert results == expected
