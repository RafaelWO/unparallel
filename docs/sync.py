import httpx
from tqdm import tqdm


def main():
    url = "https://httpbin.org"
    paths = [f"/get?i={i}" for i in range(20)]
    results = [
        httpx.get(f"{url}{path}") for path in tqdm(paths, desc="Making sync requests")
    ]
    assert len(results) == 20


if __name__ == "__main__":
    main()
