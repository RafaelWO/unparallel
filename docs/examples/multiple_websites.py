"""
This script is based on a use case at StackOverflow and fetches the content of various 
webpages.

See Also:
    https://stackoverflow.com/a/57129241
"""
import asyncio
from pprint import pp

import httpx

from unparallel import up

websites = """https://google.com/
https://youtube.com/
https://facebook.com/
https://twitter.com/
https://wikipedia.org/
https://instagram.com/
https://reddit.com/
https://amazon.com/
https://duckduckgo.com/
https://yahoo.com/
https://tiktok.com/
https://bing.com/
https://yahoo.co.jp/
https://weather.com/
https://whatsapp.com/
https://yandex.ru/
https://openai.com/
https://live.com/
https://microsoft.com/
https://microsoftonline.com/
https://linkedin.com/
https://quora.com/
https://twitch.tv/
https://naver.com/
https://netflix.com/
https://office.com/
https://vk.com/
https://globo.com/
https://Aliexpress.com/
https://cnn.com/
https://zoom.us/
https://imdb.com/
https://x.com/
https://newyorktimes.com/
https://onlyfans.com/
https://espn.com/
https://amazon.co.jp/
https://pinterest.com/
https://uol.com.br/
https://ebay.com/
https://marca.com/
https://canva.com/
https://spotify.com/
https://bbc.com/
https://paypal.com/
https://apple.com/"""


async def main():
    urls = websites.split("\n")

    # Get all pages
    results = await up(urls, method="GET", response_fn=lambda x: x.text)
    for url, content in zip(urls, results[:5]):
        print(url, content[:100])


results = asyncio.run(main())
