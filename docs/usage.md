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
to `up(...)` and add some data. 

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


## Other HTTP methods

!!! warning

    Currently (version `0.1.0`) the method `.json()` is called on every response.
    Hence, HTTP methods that don't return a JSON body will not work as expected.

Besides the popular GET and POST methods, you can use any other HTTP method supported 
by HTTPX - which are `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `PATCH`, and `OPTIONS`.
