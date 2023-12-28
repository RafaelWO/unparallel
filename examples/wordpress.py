"""
This script uses the WordPress API to query (all) posts of the website
https://techcrunch.com

See Also:
    https://developer.wordpress.org/rest-api/reference/posts/
"""
import asyncio
from pprint import pp

import httpx

from unparallel import up


async def main():
    page_size = 20
    url = "https://techcrunch.com/wp-json/wp/v2"
    pagination_url = f"{url}/posts?per_page={page_size}"

    # Get page count
    page_size = 20
    response = httpx.head(pagination_url)
    total_pages = int(response.headers["X-WP-TotalPages"])
    print(f"Website '{url}' has {total_pages} pages (page size = {page_size})")

    # Comment the line below to get all pages
    total_pages = min(total_pages, 1000)

    # Get all pages
    paths = [f"{pagination_url}&page={i}" for i in range(1, total_pages + 1)]
    return await up(url, paths, method="GET", flatten_result=True)


results = asyncio.run(main())
intersting_keys = ["id", "date", "slug", "title", "author"]
pp([{k: v for k, v in item.items() if k in intersting_keys} for item in results[:5]])
