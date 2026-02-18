import argparse
import pandas as pd
import yfinance as yf


def _flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    # yfinance can return MultiIndex columns like ('Open', 'INFY.NS')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df


def fetch_one(ticker: str, out: str, period: str = "5d", interval: str = "5m"):
    df = yf.download(
        tickers=ticker,
        interval=interval,
        period=period,
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by="column",  # helps keep columns in a consistent shape
    )

    if df is None or df.empty:
        raise ValueError(
            f"No data returned for {ticker}. Try --period 1d or try again later."
        )

    df = _flatten_cols(df).reset_index()

    # Some versions use 'Datetime', some 'Date'
    ts_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else None)
    if ts_col is None:
        raise ValueError(f"Could not find Datetime/Date column. Columns: {list(df.columns)}")

    # Ensure the OHLCV columns exist
    need = ["Open", "High", "Low", "Close", "Volume"]
    for c in need:
        if c not in df.columns:
            raise ValueError(f"Missing column {c}. Columns: {list(df.columns)}")

    out_df = pd.DataFrame({
        "timestamp": pd.to_datetime(df[ts_col]).dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "open": pd.to_numeric(df["Open"], errors="coerce"),
        "high": pd.to_numeric(df["High"], errors="coerce"),
        "low": pd.to_numeric(df["Low"], errors="coerce"),
        "close": pd.to_numeric(df["Close"], errors="coerce"),
        "volume": pd.to_numeric(df["Volume"], errors="coerce").fillna(0),
    }).dropna(subset=["open", "high", "low", "close"])

    out_df.to_csv(out, index=False)
    print(f"saved: {out}  rows={len(out_df)}  ticker={ticker}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="e.g. INFY.NS, TCS.NS")
    ap.add_argument("--out", required=True, help="e.g. datasets/INFY_5m.csv")
    ap.add_argument("--period", default="5d", help="5d recommended for 5m")
    ap.add_argument("--interval", default="5m", help="5m")
    args = ap.parse_args()

    fetch_one(args.ticker, args.out, args.period, args.interval)


if __name__ == "__main__":
    main()

