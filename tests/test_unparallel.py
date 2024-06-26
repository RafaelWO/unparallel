import asyncio
import logging
from unittest import mock

import httpx
import pytest
from httpx import AsyncClient, Response, TimeoutException

from unparallel import up
from unparallel.unparallel import (
    DEFAULT_LIMITS,
    DEFAULT_TIMEOUT,
    RequestError,
    request_urls,
    single_request,
)

BASE_URL = "http://test.com"


def get_kwargs(*args, **kwargs):
    return kwargs


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
async def test_basic_example(respx_mock):
    def query_param_value(request, i):
        return Response(200, json={"i": i})

    respx_mock.get(url__regex=rf"{BASE_URL}/get\?i=(?P<i>\d)").mock(
        side_effect=query_param_value
    )

    paths = [f"/get?i={i}" for i in range(5)]
    results = await up(paths, method="get", base_url=BASE_URL)
    assert len(results) == 5
    assert all(res["i"] == str(i) for i, res in enumerate(results))


@pytest.mark.asyncio
async def test_up_get(caplog, respx_mock):
    caplog.set_level(logging.DEBUG)
    urls = [
        "http://test1.com/get?foo=0",
        "http://test2.com/get?foo=1",
        "http://test3.com/get?foo=2",
    ]
    for url in urls:
        key, val = url.split("?")[1].split("=")
        respx_mock.get(url).mock(return_value=Response(200, json={key: int(val)}))

    results = await up(urls, "GET")

    my_log = next(rec for rec in caplog.records if rec.module == "unparallel")
    assert "Issuing 3 GET request(s)" in my_log.message
    assert len(results) == len(urls)
    for i, (res, path) in enumerate(zip(results, urls)):
        assert res == {"foo": i}
        assert path.endswith(str(i))


@pytest.mark.asyncio
@pytest.mark.parametrize("paths", ["/post", ["/post"], ["/post"] * 5])
async def test_up_post_single_vs_multi_path(paths, respx_mock):
    payloads = [{"bar": i} for i in range(5)]
    respx_mock.post(f"{BASE_URL}/post").mock(
        side_effect=[Response(200, json=data) for data in payloads]
    )

    results = await up(paths, "post", base_url=BASE_URL, payloads=payloads)
    assert len(results) == len(payloads)
    for res, data in zip(results, payloads):
        assert res == data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payloads", [{"bar": 1}, [{"bar": 1}], [{"bar": i} for i in range(5)]]
)
async def test_up_post_single_vs_multi_payload(payloads, respx_mock):
    paths = [f"/post/{i}" for i in range(5)]
    for path in paths:
        respx_mock.post(f"{BASE_URL}{path}").mock(return_value=Response(200))

    results = await up(paths, "post", base_url=BASE_URL, payloads=payloads)
    assert len(results) == len(paths)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "flatten, expected",
    [(False, [[1, 2, 3], [4, 5, 6]]), (True, [1, 2, 3, 4, 5, 6])],
    ids=["not-flat", "flat"],
)
@mock.patch(
    "unparallel.unparallel.single_request", side_effect=[(1, [1, 2, 3]), (2, [4, 5, 6])]
)
async def test_request_urls_flat(patched_fetch, flatten, expected):
    results = await request_urls(
        urls=["/a", "/b"],
        method="get",
        base_url=BASE_URL,
        flatten_result=flatten,
    )
    assert results == expected


@pytest.mark.asyncio
async def test_up_custom_response_text(respx_mock):
    urls = ["http://test.com", "http://example.com"]
    for url in urls:
        respx_mock.get(url).mock(return_value=Response(200, text="foobar"))

    results = await up(urls, method="GET", response_fn=lambda x: x.text)

    assert results == ["foobar", "foobar"]


@pytest.mark.asyncio
async def test_up_misaligned_paths_and_payloads():
    with pytest.raises(ValueError):
        await up(
            urls=["/a", "/b"],
            method="POST",
            base_url=BASE_URL,
            payloads=[1, 2, 3],
        )


@pytest.mark.asyncio
async def test_up_wrong_method():
    with pytest.raises(ValueError):
        await up("/a", method="foobar", base_url=BASE_URL)


@pytest.mark.parametrize(
    "up_kwargs, expected_timeouts, expected_limits",
    [
        ({}, DEFAULT_TIMEOUT, DEFAULT_LIMITS),
        (
            {"timeout": 3, "max_connections": 10},
            httpx.Timeout(3),
            httpx.Limits(
                max_connections=10,
                max_keepalive_connections=DEFAULT_LIMITS.max_keepalive_connections,
            ),
        ),
        (
            {
                "timeout": 100,
                "timeouts": httpx.Timeout(2, connect=5),
                "limits": httpx.Limits(max_connections=300),
            },
            httpx.Timeout(2, connect=5),
            httpx.Limits(max_connections=300),
        ),
    ],
)
@mock.patch("unparallel.unparallel.request_urls")
@pytest.mark.asyncio
async def test_httpx_config(
    request_urls_mock, up_kwargs, expected_timeouts, expected_limits
):
    request_urls_mock.side_effect = get_kwargs

    options = await up("/bar", base_url="foobar", **up_kwargs)
    assert options["timeouts"] == expected_timeouts
    assert options["limits"] == expected_limits


@pytest.mark.parametrize(
    "up_kwargs, expected_sem_value",
    [
        ({}, 100),
        ({"max_connections": 10}, 10),
        ({"max_connections": 2000}, 1000),
        ({"max_connections": None}, 1000),
        ({"semaphore_value": 42}, 42),
        ({"max_connections": 100, "semaphore_value": 42}, 42),
        ({"semaphore_value": None}, None),
    ],
)
@mock.patch("unparallel.unparallel.request_urls")
@pytest.mark.asyncio
async def test_up_semaphore_value(request_urls_mock, up_kwargs, expected_sem_value):
    request_urls_mock.side_effect = get_kwargs

    options = await up("https://example.com", **up_kwargs)

    assert options["semaphore_value"] == expected_sem_value


@pytest.mark.asyncio
async def test_up_with_client(respx_mock):
    auth = httpx.BasicAuth("foo", "bar")
    headers = {"Authorization": auth._auth_header}
    client = httpx.AsyncClient(auth=auth)
    route = respx_mock.get(BASE_URL, headers=headers)

    result = await up(BASE_URL, response_fn=None)
    assert isinstance(result[0], RequestError)

    result = await up(BASE_URL, response_fn=None, client=client)
    assert result[0].status_code == 200

    route.calls.assert_called_once()
