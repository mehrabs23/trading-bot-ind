from pathlib import Path


def cache_path(cache_dir: str, ticker: str, interval: str) -> str:
    # ticker like INFY.NS -> datasets/cache/INFY.NS_5m.csv
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    name = f"{ticker}_{interval}.csv"
    return str(Path(cache_dir) / name)

