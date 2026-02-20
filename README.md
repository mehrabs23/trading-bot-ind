# 📈 Trading Bot — Indian Markets (Intraday)

An automated intraday signal generator and backtesting engine for Indian equities (NSE). Fetches live data from Yahoo Finance, runs multiple trading strategies across the NIFTY 50 universe, and presents actionable signals through a sleek web dashboard.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **3 Strategies** | Mean Reversion, Opening Range Breakout (ORB), VWAP Reclaim |
| **Universe Scanning** | Scan all 50 NIFTY stocks in one run |
| **Backtesting Engine** | Simulates trades with SL, targets, and EOD square-off |
| **HTML Reports** | Interactive Plotly equity curves and trade logs |
| **Web Dashboard** | Dark-themed UI with signal table, filters, and candlestick charts |
| **Live Refresh** | One-click re-fetch data and regenerate signals from the dashboard |
| **Daily Automation** | `run_daily.sh` script with logging, ready for cron |
| **Risk Management** | Daily loss cap, per-trade risk sizing, entry cutoff time |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/mehrabs23/trading-bot-ind.git
cd trading-bot-ind
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Signals (Single Stock)
```bash
python main.py --mode signal --data datasets/cache/INFY.NS_5m.csv --symbol INFY
```

### 3. Generate Signals (Full Universe)
```bash
# Fetch latest 5-minute data for all NIFTY 50 stocks
python -m scripts.fetch_yahoo_bulk --universe universe/nifty50.txt --interval 5m --period 5d

# Run all strategies across the universe
python main.py --mode signal --universe universe/nifty50.txt --strategy all
```

Output: `reports/watchlist_<timestamp>.json` and `.txt`

### 4. Run Backtest
```bash
python main.py --mode backtest --universe universe/nifty50.txt --strategy all --capital 100000
```

Output: Interactive HTML report in `reports/backtests/`

---

## 🖥️ Web Dashboard

A dark-themed, real-time signal dashboard with sortable tables, strategy filters, and interactive candlestick charts.

```bash
cd dashboard
../.venv/bin/python app.py
# Open http://localhost:5000
```

**Features:**
- 📊 Stats overview — total signals, BUY/SELL split, strategy breakdown
- 🔍 Filters — by side (BUY/SELL) or strategy (MR/ORB/VWAP)
- ↕️ Sortable columns — Symbol, Entry, Time, Confidence
- 📈 Click any signal → candlestick chart with Entry/Stop/Target lines
- 🔄 **Refresh button** — fetches fresh market data and regenerates signals live

---

## ⚡ Daily Automation

Run everything in one shot:

```bash
./run_daily.sh
```

This will:
1. Fetch latest 5m data for all NIFTY 50 stocks
2. Generate signals using all strategies
3. Run backtests and save HTML reports
4. Log everything to `logs/daily_YYYY-MM-DD.log`

### Schedule with Cron
```bash
crontab -e
# Add this line (runs at 9:30 AM IST, Mon-Fri):
30 9 * * 1-5 /home/mehrab/trading-bot-ind/run_daily.sh
```

---

## 📁 Project Structure

```
trading-bot-ind/
├── main.py                  # Entry point — signal & backtest modes
├── run_daily.sh             # Daily automation script
├── requirements.txt         # Python dependencies
│
├── strategies/              # Trading strategies
│   ├── base.py              # Base Strategy class
│   ├── mean_reversion.py    # Mean Reversion (20SMA deviation)
│   ├── orb.py               # Opening Range Breakout (first 15m)
│   └── vwap.py              # VWAP Reclaim / Pullback
│
├── core/
│   ├── engine.py            # Backtesting engine (equity curve, trades)
│   └── types.py             # Signal dataclass
│
├── scripts/
│   ├── fetch_yahoo_5m.py    # Single-stock data fetcher
│   └── fetch_yahoo_bulk.py  # Bulk universe data fetcher
│
├── dashboard/
│   ├── app.py               # Flask web server
│   └── templates/index.html # Dashboard UI
│
├── reporting/
│   ├── watchlist.py          # JSON/TXT signal export
│   └── performance.py       # HTML backtest reports (Plotly)
│
├── universe/
│   └── nifty50.txt           # NIFTY 50 ticker list
│
├── data/                     # Data loaders & cache helpers
├── risk/                     # Risk management (position sizing)
├── portfolio/                # Portfolio tracking
├── execution/                # Order execution stubs
└── tests/                    # Unit tests
```

---

## 🎯 Strategies

### Mean Reversion (MR)
Signals when price deviates significantly from its 20-period SMA. BUY when oversold (below SMA by threshold), SELL when overbought.

### Opening Range Breakout (ORB)
Tracks the high/low of the first 15 minutes. Signals BUY on breakout above range high, SELL on breakdown below range low.

### VWAP Reclaim
Signals when price crosses VWAP with volume confirmation. BUY on reclaim from below, SELL on rejection from above.

---

## 📊 Signal Output Format

Each signal includes:
| Field | Description |
|-------|-------------|
| `symbol` | Stock ticker (e.g., INFY) |
| `side` | BUY or SELL |
| `entry` | Suggested entry price |
| `stop` | Stop loss level |
| `targets` | Take profit target(s) |
| `confidence` | Signal strength (0–1) |
| `reasoning` | Human-readable explanation |

---

## 🛠️ Configuration

| Argument | Default | Description |
|----------|---------|-------------|
| `--mode` | `signal` | `signal` or `backtest` |
| `--strategy` | `all` | `mr`, `orb`, `vwap`, or `all` |
| `--universe` | — | Path to ticker list file |
| `--data` | — | Path to single CSV file |
| `--symbol` | — | Ticker for single-stock mode |
| `--capital` | `100000` | Starting capital for backtest |
| `--lookback` | `20` | SMA lookback period |
| `--threshold` | `0.02` | Mean reversion deviation (2%) |

---

## 📦 Dependencies

```
pandas
yfinance
plotly
flask
matplotlib
jinja2
```

Install all: `pip install -r requirements.txt`

---

## ⚠️ Disclaimer

This bot is for **educational and research purposes only**. It does not place real trades. Always do your own analysis before making trading decisions. Past backtest performance does not guarantee future results.
