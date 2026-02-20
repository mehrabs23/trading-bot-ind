"""
Signal Dashboard - Flask web app with live refresh support.
Run: python dashboard/app.py
Then open: http://localhost:5000
"""
import json
import os
import glob
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify
import pandas as pd

app = Flask(__name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
CACHE_DIR = os.path.join(PROJECT_DIR, "datasets", "cache")
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "bin", "python3")
UNIVERSE = os.path.join(PROJECT_DIR, "universe", "nifty50.txt")

# ── Refresh job state ──────────────────────────────────────────────────────────
_job_lock = threading.Lock()
_job_state = {
    "status": "idle",   # idle | running | done | error
    "message": "",
    "started_at": None,
    "finished_at": None,
}


def _run_refresh():
    """Background thread: fetch data + generate signals."""
    global _job_state
    with _job_lock:
        _job_state.update(status="running", message="Fetching latest market data...", started_at=time.time(), finished_at=None)

    try:
        # Step 1: fetch data
        result = subprocess.run(
            [VENV_PYTHON, "-m", "scripts.fetch_yahoo_bulk",
             "--universe", UNIVERSE, "--interval", "5m", "--period", "5d"],
            cwd=PROJECT_DIR,
            capture_output=True, text=True, timeout=120,
        )
        with _job_lock:
            _job_state["message"] = "Generating signals..."

        # Step 2: generate signals
        result2 = subprocess.run(
            [VENV_PYTHON, "main.py",
             "--mode", "signal",
             "--universe", UNIVERSE,
             "--strategy", "all"],
            cwd=PROJECT_DIR,
            capture_output=True, text=True, timeout=120,
        )

        if result2.returncode != 0:
            raise RuntimeError(result2.stderr[-500:] or "Signal generation failed")

        with _job_lock:
            _job_state.update(status="done", message="Signals updated!", finished_at=time.time())

    except Exception as e:
        with _job_lock:
            _job_state.update(status="error", message=str(e)[:300], finished_at=time.time())


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_latest_watchlist():
    pattern = os.path.join(REPORTS_DIR, "watchlist_*.json")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        return [], None
    latest = files[0]
    with open(latest) as f:
        signals = json.load(f)
    fname = os.path.basename(latest)
    date_str = fname.replace("watchlist_", "").replace(".json", "")
    return signals, date_str


def load_ohlcv(symbol):
    for ticker in [f"{symbol}.NS", symbol]:
        path = os.path.join(CACHE_DIR, f"{ticker}_5m.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["timestamp"])
            return df
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    signals, date_str = load_latest_watchlist()
    total = len(signals)
    buys = sum(1 for s in signals if s["side"] == "BUY")
    sells = total - buys
    strategies = {}
    for s in signals:
        strat = s.get("reasoning", "").split("]")[0].replace("[", "").strip() if "]" in s.get("reasoning", "") else "UNKNOWN"
        strategies[strat] = strategies.get(strat, 0) + 1
    return render_template(
        "index.html",
        signals=signals,
        date_str=date_str,
        total=total,
        buys=buys,
        sells=sells,
        strategies=strategies,
    )


@app.route("/refresh", methods=["POST"])
def refresh():
    """Kick off a background refresh job."""
    with _job_lock:
        if _job_state["status"] == "running":
            return jsonify({"ok": False, "message": "Already running"}), 409
        _job_state.update(status="idle")

    t = threading.Thread(target=_run_refresh, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "Refresh started"})


@app.route("/refresh/status")
def refresh_status():
    with _job_lock:
        return jsonify(dict(_job_state))


@app.route("/signals")
def signals_json():
    signals, date_str = load_latest_watchlist()
    total = len(signals)
    buys = sum(1 for s in signals if s["side"] == "BUY")
    sells = total - buys
    strategies = {}
    for s in signals:
        strat = s.get("reasoning", "").split("]")[0].replace("[", "").strip() if "]" in s.get("reasoning", "") else "UNKNOWN"
        strategies[strat] = strategies.get(strat, 0) + 1
    return jsonify({
        "signals": signals,
        "generated": date_str,
        "total": total,
        "buys": buys,
        "sells": sells,
        "strategies": strategies,
    })


@app.route("/chart/<symbol>")
def chart_data(symbol):
    df = load_ohlcv(symbol)
    if df is None:
        return jsonify({"error": f"No data for {symbol}"}), 404
    df = df.tail(100)
    return jsonify({
        "timestamps": df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
        "open": df["open"].tolist(),
        "high": df["high"].tolist(),
        "low": df["low"].tolist(),
        "close": df["close"].tolist(),
        "volume": df["volume"].tolist(),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
