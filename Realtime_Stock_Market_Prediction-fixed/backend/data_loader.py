import yfinance as yf
import pandas as pd


def load_stock_data(ticker: str, period: str = "3y") -> pd.DataFrame:
    """
    Downloads historical OHLCV stock data.
    FIX: Handles yfinance MultiIndex columns correctly.
    FIX: Robust timezone normalization.
    """
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    except Exception as e:
        print(f"[ERROR] yfinance download failed for {ticker}: {e}")
        return pd.DataFrame()

    if df.empty:
        print(f"[WARN] No data returned for {ticker}")
        return pd.DataFrame()

    # FIX: Flatten MultiIndex columns (yfinance >= 0.2.x)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing columns {missing} for {ticker}. Got: {list(df.columns)}")
        return pd.DataFrame()

    df = df[required].copy()

    # FIX: Safe timezone strip — tz_convert(None) works on both tz-aware and naive
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert(None)

    df.dropna(inplace=True)
    return df


def load_external_factors(period: str = "3y") -> pd.DataFrame:
    """
    Downloads macroeconomic factor data.
    FIX: Safe tz handling, graceful failure per ticker, modern ffill/bfill API.
    """
    tickers = {
        "^GSPC": "Market_Index",
        "INR=X": "USD_INR",
        "GC=F":  "Gold",
        "CL=F":  "Crude_Oil",
    }

    series_list = []
    for symbol, name in tickers.items():
        try:
            df_t = yf.download(symbol, period=period, progress=False, auto_adjust=True)
            if df_t.empty:
                continue
            if isinstance(df_t.columns, pd.MultiIndex):
                df_t.columns = df_t.columns.get_level_values(0)
            close_col = next((c for c in df_t.columns if c.lower() == 'close'), None)
            if close_col is None:
                continue
            s = df_t[close_col].copy()
            s.name = name
            if s.index.tzinfo is not None:
                s.index = s.index.tz_convert(None)
            series_list.append(s)
        except Exception as e:
            print(f"[ERROR] Could not fetch macro factor {symbol}: {e}")

    if not series_list:
        return pd.DataFrame()

    factors = pd.concat(series_list, axis=1)
    factors.ffill(inplace=True)
    factors.bfill(inplace=True)
    factors.dropna(inplace=True)
    return factors
