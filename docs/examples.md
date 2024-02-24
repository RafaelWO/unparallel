This page contains some more advanced and realistic examples of using Unparallel.

## Query (all) posts of a WordPress site
```python notest
--8<-- "docs/examples/wordpress.py"
```

If you run the example, it should print something like the following:
```
Website 'https://techcrunch.com/wp-json/wp/v2' has 12202 pages (page size = 20)
Making async requests: 100%|███████████| 1000/1000 [00:13<00:00, 74.30it/s]
[{'id': 2642913,
  'date': '2023-12-26T07:05:21',
  'slug': 'vcs-are-entering-2024-with-healthy-paranoia',
  'title': {'rendered': 'VCs are entering 2024 with &#8216;healthy '
                        'paranoia&#8217;'},
  'author': 428363},
 {'id': 2645233,
  'date': '2023-12-26T06:35:00',
  'slug': 'what-vcs-are-looking-for-in-the-next-wave-of-cybersecurity-startups',
  'title': {'rendered': 'What VCs are looking for in the next wave of '
                        'cybersecurity startups'},
  'author': 133574551},
 {'id': 2641499,
  'date': '2023-12-26T06:05:55',
  'slug': 'hackers-stole-2-billion-in-crypto-in-2023-data-shows',
  'title': {'rendered': 'Hackers stole $2 billion in crypto in 2023, data '
                        'shows'},
  'author': 133574594},
 {'id': 2635851,
  'date': '2023-12-26T05:05:28',
  'slug': 'the-eternal-struggle-between-open-source-and-proprietary-software',
  'title': {'rendered': 'The eternal struggle between open source and '
                        'proprietary software'},
  'author': 133574560},
 {'id': 2645355,
  'date': '2023-12-26T03:52:55',
  'slug': 'nonprofit-code-org-sues-byjus-unit-whitehat-jr-over-payment-dues',
  'title': {'rendered': 'Nonprofit Code.org sues Byju&#8217;s unit WhiteHat Jr '
                        'over payment dues'},
  'author': 133574269}]
```

## Fetch the content of multiple websites
```python notest
--8<-- "docs/examples/multiple_websites.py"
```

If you run the example, it should print something like the following:
```
Making async requests: 100%|███████████| 43/43 [00:03<00:00, 11.60it/s]
https://www.google.com/ '<!doctype html><html itemscope="" itemtype="http://schema.org/WebPage" lang="de-AT"><head><meta cont'
https://www.youtube.com/ '<!DOCTYPE html><html style="font-size: 10px;font-family: Roboto, Arial, sans-serif;" lang="de-DE" da'
https://www.facebook.com/ '<!DOCTYPE html>\n<html lang="de" id="facebook" class="no_js">\n<head><meta charset="utf-8" /><meta nam'
https://www.wikipedia.org/ '<!DOCTYPE html>\n<html lang="en" class="no-js">\n<head>\n<meta charset="utf-8">\n<title>Wikipedia</title'
https://www.instagram.com/ '<!DOCTYPE html><html class="_9dls" lang="en" dir="ltr"><head><link data-default-icon="https://static'
```
