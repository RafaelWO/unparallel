import logging
import time
from unittest import mock

import pytest
from httpx import AsyncClient, Response, TimeoutException

from unparallel import up
from unparallel.unparallel import request_urls, single_request, sort_by_idx


def test_order_by_idx():
    to_sort = [(4, "d"), (1, "a"), (3, "c"), (2, "b")]
    expected = list("abcd")
    assert sort_by_idx(to_sort) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, method, payload",
    [
        ("http://test.com", "get", "data"),
        ("http://test.com/foo", "post", "data"),
    ],
)
async def test_single_request(url, method, payload, respx_mock):
    getattr(respx_mock, method)(url).mock(return_value=Response(200, json=payload))
    session = AsyncClient()
    result = await single_request(1, session, path=url, method=method)
    assert result == (1, payload)
    await session.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [500, 404])
async def test_single_request_fail(status, respx_mock):
    url = "http://test.com/foo"
    respx_mock.get(url).mock(return_value=Response(status))
    session = AsyncClient()
    result = await single_request(1, session, path=url, method="get")
    assert "exception" in result[1]
    await session.aclose()


@pytest.mark.asyncio
async def test_single_request_timeout(respx_mock):
    url = "http://test.com/foo"
    respx_mock.get(url).mock(side_effect=TimeoutException)
    session = AsyncClient()
    start_time = time.time()
    retries = 2
    result = await single_request(
        1, session, path=url, method="get", max_retries_on_timeout=retries
    )
    assert "exception" in result[1]
    assert time.time() - start_time > retries
    await session.aclose()


@pytest.mark.asyncio
async def test_full_run_via_httpbin():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(20)]
    results = await up(url, paths, "get", connection_limit=10)
    assert len(results) == 20
    assert all(res["args"]["i"] == str(i) for i, res in enumerate(results))


@pytest.mark.asyncio
async def test_up_get(caplog, respx_mock):
    caplog.set_level(logging.DEBUG)
    base_url = "http://test.com"
    paths = ["/get?foo=0", "/get?foo=1", "/get?foo=2"]
    for path in paths:
        key, val = path.split("?")[1].split("=")
        respx_mock.get(base_url + path).mock(
            return_value=Response(200, json={key: int(val)})
        )

    results = await up(base_url, paths, "get")

    my_log = next(rec for rec in caplog.records if rec.module == "unparallel")
    assert "Issuing 3 GET request(s)" in my_log.message
    assert len(results) == len(paths)
    for i, (res, path) in enumerate(zip(results, paths)):
        assert res == {"foo": i}


@pytest.mark.asyncio
@pytest.mark.parametrize("paths", ["/post", ["/post"], ["/post"] * 5])
async def test_up_post(paths, respx_mock):
    base_url = "http://test.com"
    payloads = [{"bar": i} for i in range(5)]
    respx_mock.post(base_url + "/post").mock(
        side_effect=[Response(200, json=data) for data in payloads]
    )

    results = await up(base_url, paths, "post", payloads=payloads)
    assert len(results) == len(payloads)
    for res, data in zip(results, payloads):
        assert res == data


@pytest.mark.asyncio
@mock.patch(
    "unparallel.unparallel.single_request", side_effect=[(1, [1, 2, 3]), (2, [4, 5, 6])]
)
async def test_request_urls_flat(patched_fetch):
    results = await request_urls(
        "http://test.com", paths=["/a", "/b"], method="get", flatten_result=True
    )
    # without flatten, result would be: [[1, 2, 3], [4, 5, 6]]
    assert results == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_up_misaligned_paths_and_payloads():
    with pytest.raises(ValueError):
        await up(
            "http://test.com", paths=["/a", "/b"], method="post", payloads=[1, 2, 3]
        )


@pytest.mark.asyncio
async def test_up_wrong_method():
    with pytest.raises(ValueError):
        await up("http://test.com", paths="/a", method="foobar")
