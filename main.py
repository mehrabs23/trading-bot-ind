import argparse
import os
from dataclasses import replace
from datetime import datetime

from core.types import RunMode
from core.engine import Engine
from data.ingestion import load_csv
from data.universe import load_universe
from data.cache import cache_path
from strategies.mean_reversion import MeanReversionStrategy
from strategies.orb import ORBStrategy
from strategies.vwap import VWAPStrategy
from reporting.performance import generate_html_report
from reporting.watchlist import save_watchlist, save_watchlist_table


def get_strategy(name, symbol, lookback, threshold, orb_minutes=15):
    if name == "mr":
        return MeanReversionStrategy(symbol, lookback=lookback, threshold=threshold)
    elif name == "orb":
        return ORBStrategy(symbol, orb_minutes=orb_minutes)
    elif name == "vwap":
        return VWAPStrategy(symbol)
    else:
        raise ValueError(f"Unknown strategy: {name}")


def run_one_csv(mode, csv_path, symbol, capital, strategy_name, **kwargs):
    bars = load_csv(csv_path, symbol)
    strat = get_strategy(strategy_name, symbol, kwargs.get('lookback', 20), kwargs.get('threshold', 0.02), kwargs.get('orb_minutes', 15))
    eng = Engine(strat, mode, initial_capital=capital)
    res = eng.run(bars)
    return eng, res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", type=str, choices=["signal", "backtest"], default="signal")

    # make optional
    ap.add_argument("--data", type=str, help="CSV path (single mode)")
    ap.add_argument("--symbol", type=str, help="symbol (single mode)")

    ap.add_argument("--capital", type=float, default=100000.0)

    ap.add_argument("--universe", type=str, default="", help="path to universe txt (optional)")
    ap.add_argument("--cache_dir", type=str, default="datasets/cache")
    ap.add_argument("--period", type=str, default="5d")
    ap.add_argument("--interval", type=str, default="5m")
    
    # Strategy selection
    ap.add_argument("--strategy", type=str, choices=["mr", "orb", "vwap", "all"], default="mr")

    # Filters
    ap.add_argument("--min_avg_volume", type=float, default=0.0)
    ap.add_argument("--min_avg_value", type=float, default=0.0)
    ap.add_argument("--min_atr", type=float, default=0.0)
    ap.add_argument("--time_start", type=str, default=None, help="HH:MM")
    ap.add_argument("--time_end", type=str, default=None, help="HH:MM")
    
    # Reporting
    ap.add_argument("--report_dir", type=str, default="reports/backtests")

    # Strategy Params
    ap.add_argument("--mr_lookback", type=int, default=20)
    ap.add_argument("--mr_threshold", type=float, default=0.02)
    ap.add_argument("--orb_minutes", type=int, default=15)

    args = ap.parse_args()
    mode = RunMode(args.mode.upper())

    # Validation
    has_universe = bool(args.universe)
    has_single = bool(args.data and args.symbol)
    
    if not has_universe and not has_single:
        ap.error("Must provide either --universe OR (--data and --symbol)")
    
    if args.data and not args.symbol:
        ap.error("--data requires --symbol")
    if args.symbol and not args.data:
        ap.error("--symbol requires --data")

    # Time parsing
    t_start, t_end = None, None
    if args.time_start:
        t_start = datetime.strptime(args.time_start, "%H:%M").time()
    if args.time_end:
        t_end = datetime.strptime(args.time_end, "%H:%M").time()

    strategies_to_run = ["mr", "orb", "vwap"] if args.strategy == "all" else [args.strategy]

    # ---- universe mode ----
    if args.universe:
        tickers = load_universe(args.universe)
        all_signals = []
        
        # Backtest Aggregation
        agg_trades = []
        agg_equity = [] # This is tricky for universe. We'll simplify: just sum PnL? 
                        # Real portfolio backtest requires time-sync.
                        # For now, let's collect all trades and PnL.
        
        total_pnl = 0.0
        
        print(f"Running {mode.name} for {len(tickers)} symbols...")

        for t in tickers:
            sym = t.replace(".NS", "")
            csv_path = cache_path(args.cache_dir, t, args.interval)

            try:
                if not os.path.exists(csv_path):
                    from scripts.fetch_yahoo_5m import fetch_one
                    fetch_one(t, csv_path, args.period, args.interval)

                for strat_name in strategies_to_run:
                    eng, res = run_one_csv(
                        mode=mode,
                        csv_path=csv_path,
                        symbol=sym,
                        capital=args.capital, # Note: Separate capital per symbol in this simple loop
                        strategy_name=strat_name,
                        lookback=args.mr_lookback,
                        threshold=args.mr_threshold,
                        orb_minutes=args.orb_minutes
                    )

                    if mode == RunMode.SIGNAL:
                        # Apply filters (existing logic)
                        for sig in eng.signals:
                            meta = sig.meta or {}
                            
                            if meta.get("avg_volume", 0) < args.min_avg_volume:
                                continue
                            if meta.get("avg_value", 0) < args.min_avg_value:
                                continue
                            if meta.get("atr", 0) < args.min_atr:
                                continue
                            
                            ts_time = sig.timestamp.time()
                            if t_start and ts_time < t_start:
                                continue
                            if t_end and ts_time > t_end:
                                continue
                                
                            # Add strategy name to meta/reasoning
                            sig = replace(sig, reasoning=f"[{strat_name.upper()}] {sig.reasoning}")
                            all_signals.append(sig)
                    
                    else:
                        # BACKTEST Mode aggregation
                        # We are running independent simulated backtests.
                        # We will aggregate all trades.
                        agg_trades.extend(res['trades'])
                        total_pnl += res['realized_pnl']
                        # Ensure equity curve is not empty before extending
                        if res.get('equity_curve'):
                            agg_equity.extend(res['equity_curve']) 
            except Exception as e:
                print(f"ERROR processing {t}: {e}")
                continue 

        if mode == RunMode.SIGNAL:
            # Sort: (-confidence, -avg_volume, -atr, symbol)
            all_signals.sort(key=lambda s: (
                -float(s.confidence),
                -float(s.meta.get("avg_volume", 0) if s.meta else 0),
                -float(s.meta.get("atr", 0) if s.meta else 0),
                s.symbol
            ))

            path_json = save_watchlist(all_signals)
            path_txt = save_watchlist_table(all_signals)
            print(f"\nSaved watchlist JSON: {path_json}")
            print(f"Saved watchlist table: {path_txt}")
            print(f"Total signals: {len(all_signals)}")
            return
        
        else:
            # Backtest Report
            os.makedirs(args.report_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            report_path = os.path.join(args.report_dir, f"report_{timestamp}.html")
            
            # Simple aggregation stats
            wins = [t for t in agg_trades if t['pnl_est'] > 0]
            win_rate = len(wins) / len(agg_trades) if agg_trades else 0.0
            
            # For equity curve, merging multiple independent backtests is complex.
            # We will just plot one concatenating or maybe just show Total PnL.
            # To do it right, we'd need a Portfolio object managing all tickers at once.
            # For Phase 2 simple version: We will pass an empty equity curve if aggregated, 
            # OR better: create a synthetic daily equity curve by summing daily PnL?
            # Let's just pass the raw trades for now, and maybe a dummy equity curve of just final points.
            
            stats = {
                "final_equity": args.capital + total_pnl, # Mock estimate
                "realized_pnl": total_pnl,
                "num_trades": len(agg_trades),
                "win_rate": win_rate
            }
            
            # For universe, let's just use the first symbol's curve or empty for now to avoid misleading graphs
            # unless we implement time-aligned summation.
            # Implementation Plan said "Aggregate results".
            # Let's try to pass the raw list. generate_html_report sorts by timestamp. 
            # If we pass ALL equity points from ALL symbols, it will look chaotic but "correct" in time.
            # Actually, calculate_drawdown assumes a single series. 
            # Lets just pass an empty curve for universe mode for now, focusing on Trade List.
            
            generate_html_report(stats, [], agg_trades, report_path)
            print(f"\nSaved Backtest Report: {report_path}")
            print(f"Total PnL: {total_pnl:.2f}")
            print(f"Trades: {len(agg_trades)}")
            print(f"Win Rate: {win_rate*100:.1f}%")
            return

    # ---- single symbol mode ----
    # Just run first selected strategy or all? Single mode usually creates one report.
    # If "all", we might print multiple summaries.
    
    os.makedirs(args.report_dir, exist_ok=True)
    
    for strat_name in strategies_to_run:
        print(f"\n--- Strategy: {strat_name.upper()} ---")
        eng, res = run_one_csv(
            mode=mode,
            csv_path=args.data,
            symbol=args.symbol,
            capital=args.capital,
            strategy_name=strat_name,
            lookback=args.mr_lookback,
            threshold=args.mr_threshold,
            orb_minutes=args.orb_minutes
        )

        if mode == RunMode.SIGNAL:
            path = save_watchlist(eng.signals)
            print(f"Saved watchlist: {path}")
            print(f"Signals: {res['num_signals']}")
        else:
            # Generate Report per strategy
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            report_path = os.path.join(args.report_dir, f"report_{args.symbol}_{strat_name}_{timestamp}.html")
            
            generate_html_report(res, res['equity_curve'], res['trades'], report_path)
            
            print("==== BACKTEST SUMMARY ====")
            print("Final Equity:", res["final_equity"])
            print("Realized PnL:", res["realized_pnl"])
            print("Trades:", res["num_trades"])
            print(f"Report: {report_path}")

if __name__ == "__main__":
    main()

