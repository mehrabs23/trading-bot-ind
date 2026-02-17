import csv
from datetime import datetime
from typing import List
from core.types import MarketBar


def load_csv(path: str, symbol: str) -> List[MarketBar]:
    bars: List[MarketBar] = []
    with open(path, "r", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            # expected timestamp ISO: 2026-02-17T09:15:00
            ts = datetime.fromisoformat(row["timestamp"])
            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    return bars

