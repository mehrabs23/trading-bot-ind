import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path


def save_watchlist(signals, out_dir="reports"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = Path(out_dir) / f"watchlist_{ts}.json"

    payload = []
    for s in signals:
        d = asdict(s)
        d["timestamp"] = s.timestamp.isoformat()
        payload.append(d)

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    return str(path)


def save_watchlist_table(signals, out_dir="reports"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = Path(out_dir) / f"watchlist_{ts}.txt"

    lines = []
    lines.append("RANK | TIME | SYMBOL | SIDE | CONF | ENTRY | STOP | TARGETS | REASON")
    lines.append("-" * 150)

    for i, s in enumerate(signals, 1):
        targets = ",".join(f"{x:.2f}" for x in s.targets[:3])
        ts_str = s.timestamp.strftime("%H:%M")
        lines.append(
            f"{i:>4} | {ts_str} | {s.symbol:<10} | {s.side.value:<4} | {s.confidence:>4.2f} | "
            f"{s.entry:>10.2f} | {s.stop:>10.2f} | {targets:<18} | {s.reasoning}"
        )

    path.write_text("\n".join(lines))
    return str(path)


