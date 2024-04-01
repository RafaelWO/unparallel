import httpx
from tqdm import tqdm

NUM_REQUESTS = 20


def main():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(NUM_REQUESTS)]
    results = [
        httpx.get(f"{url}{path}") for path in tqdm(paths, desc="Making sync requests")
    ]
    assert len(results) == NUM_REQUESTS


if __name__ == "__main__":
    main()
