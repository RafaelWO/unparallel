import logging
import re
import time
from unittest import mock

import pytest
from httpx import AsyncClient, Response

from unparallel.unparallel import MAX_TRIALS, order_by_idx, request_urls, single_request


def test_order_by_idx():
    to_sort = [(4, "d"), (1, "a"), (3, "c"), (2, "b")]
    expected = list("abcd")
    assert order_by_idx(to_sort) == expected


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
@pytest.mark.parametrize("status", [None, 404])
async def test_single_request_fail(status, respx_mock):
    url = "http://test.com/foo"
    respx_mock.get(url).mock(return_value=Response(status))
    start_time = time.time()
    session = AsyncClient()
    result = await single_request(1, session, path=url, method="get")
    assert "exception" in result[1]
    assert time.time() - start_time > MAX_TRIALS
    await session.aclose()


@pytest.mark.asyncio
async def test_full_run_via_httpbin():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(100)]
    results = await request_urls(url, paths, "get")
    assert len(results) == 100
    assert all(res["args"]["i"] == str(i) for i, res in enumerate(results))


@pytest.mark.asyncio
async def test_request_urls_get(caplog, respx_mock):
    caplog.set_level(logging.DEBUG)
    base_url = "http://test.com"
    paths = ["/get?foo=0", "/get?foo=1", "/get?foo=2"]
    for path in paths:
        respx_mock.get(base_url + path).mock(
            return_value=Response(200, json=eval(f"dict({path.split('?')[1]})"))
        )

    results = await request_urls(base_url, paths, "get")

    my_log = next(rec for rec in caplog.records if rec.module == "unparallel")
    assert "Issuing 3 GET request(s)" in my_log.message
    assert len(results) == len(paths)
    for i, (res, path) in enumerate(zip(results, paths)):
        assert res == {"foo": i}


# @pytest.mark.asyncio
# @pytest.mark.parametrize("paths", ["/post", ["/post"], ["/post"] * 5])
# async def test_request_urls_post(paths, respx_mock):
#     base_url = "http://test.com"
#     payloads = [{"bar": i} for i in range(5)]
#     respx_mock.post(base_url + "/post").mock(
#         side_effect=[Response(200, json=data) for data in payloads]
#     )

#     results = await request_urls(base_url, paths, "post", payloads=payloads)
#     assert len(results) == len(payloads)
#     for res, data in zip(results, payloads):
#         assert res == data


@pytest.mark.asyncio
async def test_request_urls_misaligned_paths_and_payloads():
    with pytest.raises(ValueError):
        await request_urls(
            "http://test.com", paths=["/a", "/b"], method="post", payloads=[1, 2, 3]
        )


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
