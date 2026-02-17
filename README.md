# AI Bot for Indian Markets (Intraday-first)

Current features:
- Signal assistant (from 5-min CSV)
- Intraday backtest simulator (SL + EOD squareoff)
- Risk governor (daily loss cap, risk-per-trade sizing, entry cutoff)
- Watchlist JSON output

## CSV format
timestamp,open,high,low,close,volume
2026-02-17T09:15:00,100,102,99,101,50000

## Run
Signal:
python main.py --mode signal --data data/INFY_5m.csv --symbol INFY

Backtest:
python main.py --mode backtest --data data/INFY_5m.csv --symbol INFY --capital 100000

