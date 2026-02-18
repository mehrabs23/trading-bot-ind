import argparse
from pathlib import Path

from data.universe import load_universe
from data.cache import cache_path
from scripts.fetch_yahoo_5m import fetch_one


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True, help="e.g. universe/nifty50.txt")
    ap.add_argument("--cache_dir", default="datasets/cache", help="where to save csvs")
    ap.add_argument("--period", default="5d")
    ap.add_argument("--interval", default="5m")
    args = ap.parse_args()

    tickers = load_universe(args.universe)
    Path(args.cache_dir).mkdir(parents=True, exist_ok=True)

    ok = 0
    fail = 0

    for t in tickers:
        out = cache_path(args.cache_dir, t, args.interval)
        try:
            fetch_one(t, out, args.period, args.interval)
            ok += 1
        except Exception as e:
            print(f"[FAIL] {t}: {e}")
            fail += 1

    print(f"\nDONE: ok={ok} fail={fail} cache_dir={args.cache_dir}")


if __name__ == "__main__":
    main()


