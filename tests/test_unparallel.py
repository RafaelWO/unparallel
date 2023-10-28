import time

import pytest
from httpx import AsyncClient, Response

from unparallel.unparallel import order_by_idx, single_request, MAX_TRIALS


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
    ]
)
async def test_single_request(url, method, payload, respx_mock):
    getattr(respx_mock, method)(url).mock(return_value=Response(200, json=payload))
    session = AsyncClient()
    result = await single_request(1, session, path=url, method=method)
    assert result == (1, payload)
    await session.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [None, 404]
)
async def test_single_request_fail(status, respx_mock):
    url = "http://test.com/foo"
    respx_mock.get(url).mock(return_value=Response(status))
    start_time = time.time()
    session = AsyncClient()
    result = await single_request(1, session, path=url, method="get")
    assert "exception" in result[1]
    assert time.time() - start_time > MAX_TRIALS
    await session.aclose()

#
# @pytest.mark.asyncio
# async def test_single_request_401():
#     url = "http://test.com/foo"
#     with aioresponses() as aio_mock:
#         aio_mock.get(url, status=401)
#         session = ClientSession(raise_for_status=True)
#         with pytest.raises(ConnectionError):
#             await async_utils.single_request(1, session, path=url, method="get")
#         await session.close()
#
#
# @pytest.mark.asyncio
# async def test_request_urls_get(capfd):
#     base_url = "http://test.com"
#     paths = ["/get?foo=0", "/get?foo=1", "/get?foo=2"]
#     with aioresponses() as aio_mock:
#         for path in paths:
#             aio_mock.get(path, payload=eval(f"dict({path.split('?')[1]})"))
#
#         results = await async_utils.request_urls(base_url, paths, "get", verbose=True)
#         out, err = capfd.readouterr()
#         assert "Issuing 3 GET request(s)" in out
#         assert len(results) == len(paths)
#         for i, (res, path) in enumerate(zip(results, paths)):
#             assert res == {"foo": i}
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "paths", [
#         "/post",
#         ["/post"],
#         ["/post"] * 5
#     ]
# )
# async def test_request_urls_post(paths):
#     base_url = "http://test.com"
#     payloads = [{"bar": i} for i in range(5)]
#     with aioresponses() as aio_mock:
#         for data in payloads:
#             aio_mock.post("/post", payload=data)
#
#         results = await async_utils.request_urls(base_url, paths, "post", payloads=payloads, verbose=True)
#         assert len(results) == len(payloads)
#         for i, (res, data) in enumerate(zip(results, payloads)):
#             assert res == data
#
#
# @pytest.mark.asyncio
# async def test_request_urls_fail():
#     with pytest.raises(RuntimeError):
#         await async_utils.request_urls("http://test.com", paths=["/a", "/b"], method="post", payloads=[1, 2, 3])
#
#
# @pytest.mark.asyncio
# @mock.patch("async_utils.bound_fetch", side_effect=[(1, [1, 2, 3]), (2, [4, 5, 6])])
# async def test_request_urls_flat(patched_fetch):
#     results = await async_utils.request_urls("http://test.com", paths=["/a", "/b"], method="get", flatten_result=True)
#     # without flatten, result would be: [[1, 2, 3], [4, 5, 6]]
#     assert results == [1, 2, 3, 4, 5, 6]
#
#
# @pytest.mark.parametrize(
#     "pat_limit, params", [
#         [0, None],
#         [60, {"foo": "bar"}],
#         [45, None]
#     ]
# )
# def test_get_patients_async(requests_mock, pat_limit: int, params: dict):
#     api = BackendApi("http://test.com")
#     ps = 10
#     total_count = 100
#     with aioresponses() as aio_mock:
#         # Request for patient count is done synchronously via 'requests' -> we use 'requests_mock' for this
#         requests_mock.get(api.base_url + "/fhir/patients/count", json=total_count)
#
#         _params = {"limit": ps, "skip": "\d"}
#         if params:
#             _params.update(params)
#         _params = {k: _params[k] for k in sorted(_params.keys())}
#         url_pattern = rf"^/fhir/patients/\?" + urlencode(_params, safe="\\")
#
#         aio_mock.get(re.compile(url_pattern), payload=[1]*10, repeat=True)
#
#         token = {"token_type": "bearer", "access_token": "123"}
#         results = async_utils.get_patients_async(api, token=token, page_size=ps, limit=pat_limit, params=params)
#         expected = round(pat_limit, -1) if pat_limit else total_count
#         assert sum(results) == expected
