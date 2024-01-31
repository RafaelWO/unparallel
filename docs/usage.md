A basic use case for Unparallel could be fetching some JSON data from a REST API 
asynchronously.
In the example below, we issue 100 GET requests with different query parameters.

```python
import asyncio

from unparallel import up

async def main():
    url = "https://httpbin.org"
    paths = [f"/get?foo={i}" for i in range(100)]
    return await up(url, paths)

results = asyncio.run(main())
print([item["args"] for item in results[:5]])
```

This prints:
```
Making async requests: 100%|███████████| 100/100 [00:01<00:00, 99.94it/s]
[{'foo': '0'}, {'foo': '1'}, {'foo': '2'}, {'foo': '3'}, {'foo': '4'}]
```

## POSTing Data
### One body for different paths
If you want to do POST instead of GET requests, you just have to pass `method='POST'`
to `up()` and add some data. 

```python
import asyncio
from pprint import pp

from unparallel import up

async def main():
    url = "https://httpbin.org"
    data = {"item_id": 1, "type": "tree"}
    paths = [f"/post?bar={i}" for i in range(100)]
    return await up(url, paths, method="POST", payloads=data)

results = asyncio.run(main())
pp([{"args": item["args"], "data": item["data"]} for item in results[:5]])
```

This prints:
```
Making async requests: 100%|███████████| 100/100 [00:01<00:00, 63.40it/s]
[{'args': {'bar': '0'}, 'data': '{"item_id": 1, "type": "tree"}'},
 {'args': {'bar': '1'}, 'data': '{"item_id": 1, "type": "tree"}'},
 {'args': {'bar': '2'}, 'data': '{"item_id": 1, "type": "tree"}'},
 {'args': {'bar': '3'}, 'data': '{"item_id": 1, "type": "tree"}'},
 {'args': {'bar': '4'}, 'data': '{"item_id": 1, "type": "tree"}'}]
```

### Different bodies for one path
As you might not need different query parameters for your POST URL, i.e. you have only
one URL/path, but you want to POST a list of different JSON bodies, this is also 
supported.


```python
import asyncio
from pprint import pp

from unparallel import up

async def main():
    url = "https://httpbin.org"
    path = "/post"
    data = [{"type": "tree", "height": i} for i in range(100)]
    return await up(url, path, method="POST", payloads=data)

results = asyncio.run(main())
pp([item["data"] for item in results[:5]])
```

This prints:
```
Making async requests: 100%|███████████| 100/100 [00:01<00:00, 63.40it/s]
['{"type": "tree", "height": 0}',
 '{"type": "tree", "height": 1}',
 '{"type": "tree", "height": 2}',
 '{"type": "tree", "height": 3}',
 '{"type": "tree", "height": 4}']
```

## Custom response functions
Per default, Unparallel will call the `.json()` function on every `httpx.Response` and 
return the result. But you might want to get other data from the response like the 
content as plain-text or the HTTP status. 

For this, define your own response function/callback using a `def` or `lambda` and pass
it to `up()` via the keyword `response_fn`. The function will receive a `httpx.Response`
object as the argument and can return anything.

If you want to process the raw `httpx.Response` later yourself, you can simply set 
`response_fn=None`.

The example below demonstrates how to use a custom response function to get the `.text`
of a response:

```python hl_lines="11"
import asyncio

from unparallel import up

async def main():
    urls = [
        "https://www.example.com",
        "https://duckduckgo.com/",
        "https://github.com"
    ]
    return await up(urls, response_fn=lambda x: x.text)

results = asyncio.run(main())
for res in results:
    print(repr(res[:50]))
```

This should print something similar to the following:
```
Making async requests: 100%|███████████| 3/3 [00:00<00:00,  4.43it/s]
'<!doctype html>\n<html>\n<head>\n    <title>Example D'
'<!DOCTYPE html><html lang="en-US"><head><meta char'
'\n\n\n\n\n\n<!DOCTYPE html>\n<html\n  lang="en"\n  \n  \n  da'
```

## Other HTTP methods
Besides the popular GET and POST methods, you can use any other HTTP method supported 
by HTTPX - which are `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `PATCH`, and `OPTIONS`.

For example, you can get the status of services/webpages using the method `HEAD` in
combination with a custom response function:

```python hl_lines="11"
import asyncio

from unparallel import up

async def main():
    urls = [
        "https://www.example.com",
        "https://duckduckgo.com/",
        "https://github.com"
    ]
    return await up(urls, method="HEAD", response_fn=lambda x: x.status_code)

results = asyncio.run(main())
print(results)
```

This prints:
```
Making async requests: 100%|███████████| 3/3 [00:00<00:00,  4.43it/s]
[200, 200, 200]
```


## Pagination and flattening
Another use case for Unparallel could be fetching all items from a REST API using 
pagination. This is useful if there are too many objects to get them all at once and 
you want to avoid making a single request for every item.

Let's say you want to list 1000 items from this [University Domains and Names API](https://github.com/Hipo/university-domains-list-api).
This API supports pagination via the query parameters
`offset` and `limit`.

```python
import asyncio
from pprint import pp

from unparallel import up

async def main():
    url = "http://universities.hipolabs.com"
    paths = [f"/search?limit=20&offset={i}" for i in range(0, 1000, 20)]
    return await up(url, paths)

results = asyncio.run(main())
print(f"#Results: {len(results)}")
pp([(type(item), len(item)) for item in results[:5]])
```

This prints:
```
#Results: 50
[(<class 'list'>, 20),
 (<class 'list'>, 20),
 (<class 'list'>, 20),
 (<class 'list'>, 20),
 (<class 'list'>, 20)]
```

Because we get a page (list of items) per request, the number of objects in `results`
is 50 (1000/20) and the university metadata is within a nested array structure:

```
[
    [
        {
            "name": "Kharkiv National University",
            "country": "Ukraine",
            "alpha_two_code": "UA",
            ...
        },
        # ... 19 more items
    ],
    [
        ... # next page of 20 items
    ],
    ...
]
```

But in most cases, you would want just one list of all objects (universities), i.e. a
flattened array. Unparallel will flatten the data for you if you pass 
`flatten_result=True`.

```python hl_lines="9"
import asyncio
from pprint import pp

from unparallel import up

async def main():
    url = "http://universities.hipolabs.com"
    paths = [f"/search?limit=20&offset={i}" for i in range(0, 1000, 20)]
    return await up(url, paths, flatten_result=True)

results = asyncio.run(main())
print(f"#Results: {len(results)}")
pp([(type(item), len(item)) for item in results[:5]])
pp(results[:2])
```

This prints:
```
#Results: 1000
[(<class 'dict'>, 6),
 (<class 'dict'>, 6),
 (<class 'dict'>, 6),
 (<class 'dict'>, 6),
 (<class 'dict'>, 6)]
[{'name': 'Kharkiv National University',
  'country': 'Ukraine',
  'alpha_two_code': 'UA',
  'domains': ['student.karazin.ua', 'karazin.ua'],
  'web_pages': ['https://karazin.ua'],
  'state-province': None},
 {'name': 'Universidad Técnica Federico Santa María',
  'country': 'Chile',
  'alpha_two_code': 'CL',
  'domains': ['usm.cl'],
  'web_pages': ['https://usm.cl'],
  'state-province': None}]
```

## Configuring limits and timeouts
You can configure connection pool limits and request timeouts using the following 
parameters in the `up()` method:

* `max_connections (int)`: The total number of simultaneous TCP connections. This is passed into `httpx.Limits()` and defaults to 100.
* `limits (Optional[httpx.Limits])`: Explicitly set the HTTPX limits configuration. This overrides `max_connections`.
* `timeout (int)`: The timeout for requests in seconds. This is passed into `httpx.Timeout()` and defaults to 10.
* `timeouts (Optional[httpx.Timeout])`: Explicitly set the HTTPX timeout configuration. This overrides `timeout`.

If you don't care about a detailed timeout or limits configuration, you can use 
`up()` without specifying any of those options:

```python
results = await up(base_url, paths)
```

Otherwise, you can use the simplified parameters `max_connections` for setting the 
connection limit and/or `timeout` for setting (all) timeouts for requests:


```python
results = await up(base_url, paths, max_connections=10, timeout=60)
```

This results in the limits config created via `httpx.Limits(max_connections=10, **default_values)`
and timeout config created via `httpx.Timeout(60)`

For more fine-grained control over limits and timeouts, just specify the HTTPX configs 
and pass them to `up()`:

```python
results = await up(
    base_url, 
    paths, 
    limits=httpx.Limits(max_connections=20, ...), 
    timeouts=httpx.Timeout(connect=5, ...)
)
```

## Retries
Per default, every HTTP request will be retried 3 times if an exception of the type 
`httpx.TimeoutException` is raised. You can change the behavior by passing e.g. 
`max_retries_on_timeout=5` to `up()` for doing 5 retries, or pass `0` for disabling them.

## Progress bar
Unparallel uses [tqdm](https://github.com/tqdm/tqdm/) to display the progress of the 
HTTP requests - specifically [`tqdm.asyncio.tqdm.as_completed()`](https://tqdm.github.io/docs/asyncio/#as_completed) 
is used to iterate over the list of async tasks (HTTP requests).

You can disable the progress bar by passing `progress=False` to `up()`.
