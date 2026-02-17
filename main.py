import argparse
from core.types import RunMode
from core.engine import Engine
from data.ingestion import load_csv
from strategies.mean_reversion import MeanReversionStrategy
from reporting.watchlist import save_watchlist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", type=str, choices=["signal", "backtest"], default="signal")
    ap.add_argument("--data", type=str, required=True, help="CSV with 5-min bars")
    ap.add_argument("--symbol", type=str, required=True)
    ap.add_argument("--capital", type=float, default=100000.0)

    ap.add_argument("--mr_lookback", type=int, default=20)
    ap.add_argument("--mr_threshold", type=float, default=0.02)

    args = ap.parse_args()

    mode = RunMode(args.mode.upper())
    bars = load_csv(args.data, args.symbol)

    strat = MeanReversionStrategy(args.symbol, lookback=args.mr_lookback, threshold=args.mr_threshold)
    eng = Engine(strat, mode, initial_capital=args.capital)
    res = eng.run(bars)

    if mode == RunMode.SIGNAL:
        path = save_watchlist(eng.signals)
        print(f"\nSaved watchlist: {path}")
        print(f"Signals: {res['num_signals']}")
    else:
        print("\n==== BACKTEST SUMMARY ====")
        print("Final Equity:", res["final_equity"])
        print("Realized PnL:", res["realized_pnl"])
        print("Trades:", res["num_trades"])


main()

