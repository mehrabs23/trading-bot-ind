import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path


def save_watchlist(signals, out_dir="reports"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = Path(out_dir) / f"watchlist_{ts}.json"

    payload = [asdict(s) for s in signals]
    # datetime not JSON serializable if present in meta; we avoid it for now.

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    return str(path)

