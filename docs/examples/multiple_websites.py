"""
This script is based on a use case at StackOverflow and fetches the content of various 
webpages.

See Also:
    https://www.stackoverflow.com/a/57129241
"""
import asyncio

from unparallel import up

websites = """https://www.google.com/
https://www.youtube.com/
https://www.facebook.com/
https://www.wikipedia.org/
https://www.instagram.com/
https://www.reddit.com/
https://www.amazon.com/
https://www.duckduckgo.com/
https://www.yahoo.com/
https://www.tiktok.com/
https://www.bing.com/
https://www.yahoo.co.jp/
https://www.weather.com/
https://www.whatsapp.com/
https://www.yandex.ru/
https://www.openai.com/
https://www.live.com/
https://www.microsoft.com/
https://www.linkedin.com/
https://www.quora.com/
https://www.twitch.tv/
https://www.naver.com/
https://www.netflix.com/
https://www.office.com/
https://www.vk.com/
https://www.globo.com/
https://www.Aliexpress.com/
https://www.cnn.com/
https://www.zoom.us/
https://www.imdb.com/
https://www.x.com/
https://www.nytimes.com/
https://www.onlyfans.com/
https://www.espn.com/
https://www.amazon.co.jp/
https://www.pinterest.com/
https://www.uol.com.br/
https://www.ebay.com/
https://www.marca.com/
https://www.canva.com/
https://www.spotify.com/
https://www.bbc.com/
https://www.paypal.com/
https://www.apple.com/"""


async def main():
    urls = websites.split("\n")

    # Get all pages
    results = await up(
        urls, method="GET", response_fn=lambda x: x.text, raise_for_status=False
    )

    # Print the content of the first 5 pages
    for url, content in zip(urls, results[:5]):
        print(url, repr(content[:100]))


results = asyncio.run(main())
