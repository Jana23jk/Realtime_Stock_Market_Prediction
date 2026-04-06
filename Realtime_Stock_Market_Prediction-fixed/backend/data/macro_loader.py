import yfinance as yf
import pandas as pd


def get_macro_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches major economic indicators.
    FIX: Deprecated fillna(method=...) replaced with modern .ffill()/.bfill().
    FIX: Safe tz_localize — only strip if timezone-aware.
    FIX: Graceful per-ticker failure.
    """
    tickers = {
        "volatility":    "^VIX",
        "interest_rate": "^TNX",
        "oil":           "CL=F",
        "usd_index":     "DX-Y.NYB",
    }

    series_list = []
    for name, ticker_symbol in tickers.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            data   = ticker.history(start=start_date, end=end_date, interval="1d")

            if data.empty:
                print(f"[WARN] No macro data for {ticker_symbol}")
                continue

            data = data[['Close']].rename(columns={'Close': name})

            # FIX: Only strip tz if index is tz-aware
            if data.index.tzinfo is not None:
                data.index = data.index.tz_convert(None)

            series_list.append(data)
        except Exception as e:
            print(f"[ERROR] Macro factor {name} ({ticker_symbol}): {e}")

    if not series_list:
        return pd.DataFrame()

    macro_df = pd.concat(series_list, axis=1)

    # FIX: Modern pandas ffill/bfill API
    macro_df.ffill(inplace=True)
    macro_df.bfill(inplace=True)
    macro_df.dropna(inplace=True)

    return macro_df
