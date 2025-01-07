import logging

import httpx
import pytest
from httpx import Response

from unparallel import Up, up
from unparallel.unparallel import (
    DEFAULT_LIMITS,
    DEFAULT_TIMEOUT,
    RequestError,
)

BASE_URL = "http://test.com"


@pytest.mark.asyncio
@pytest.mark.parametrize("usage", ["up", "iter", "all"])
async def test_basic_example(usage, respx_mock):
    def query_param_value(request, i):
        return Response(200, json={"i": i})

    respx_mock.get(url__regex=rf"{BASE_URL}/get\?i=(?P<i>\d)").mock(
        side_effect=query_param_value
    )

    paths = [f"/get?i={i}" for i in range(5)]

    if usage == "up":
        results = await up(paths, method="get", base_url=BASE_URL)
    elif usage == "all":
        results = await Up(paths, method="get", base_url=BASE_URL).all()
    elif usage == "iter":
        results = []
        async for resp in Up(paths, method="get", base_url=BASE_URL):
            results.append(resp)

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
@pytest.mark.asyncio
async def test_httpx_config(up_kwargs, expected_timeouts, expected_limits):
    obj = Up("/bar", base_url="foobar", **up_kwargs)
    assert obj.timeouts == expected_timeouts
    assert obj.limits == expected_limits


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
@pytest.mark.asyncio
async def test_up_semaphore_value(up_kwargs, expected_sem_value):
    obj = Up("https://example.com", **up_kwargs)

    assert obj.semaphore_value == expected_sem_value


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
