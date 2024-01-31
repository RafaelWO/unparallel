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
from unparallel.unparallel import RequestError


async def main():
    page_size = 20
    base_url = "https://techcrunch.com/wp-json/wp/v2"
    pagination_url = f"/posts?per_page={page_size}"

    # Get page count
    page_size = 20
    response = httpx.head(base_url + pagination_url)
    total_pages = int(response.headers["X-WP-TotalPages"])
    print(f"Website '{base_url}' has {total_pages} pages (page size = {page_size})")

    # Comment the line below to get all pages. Note that you will have to adjust
    # the settings for this to work without errors. For me, it worked using
    # max_connections=800 and timeout=180

    total_pages = min(total_pages, 1000)

    # Get all pages and flatten the result
    paths = [f"{pagination_url}&page={i}" for i in range(1, total_pages + 1)]
    results = await up(paths, method="GET", base_url=base_url, flatten_result=True)

    # Check if some requests failed
    valid_results = [item for item in results if not isinstance(item, RequestError)]
    fails = len(results) - len(valid_results)
    print(f"{fails=} ({fails/len(results):.2%})")

    # Display some properties of the first 5 posts
    intersting_keys = ["id", "date", "slug", "title", "author"]
    pp(
        [
            {k: v for k, v in item.items() if k in intersting_keys}
            for item in valid_results[:5]
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
