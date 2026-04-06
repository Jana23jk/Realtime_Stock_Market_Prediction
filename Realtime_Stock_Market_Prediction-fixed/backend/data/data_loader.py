import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from .macro_loader import get_macro_data


def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetches stock OHLCV data.
    FIX: MultiIndex column flatten, safe tz strip.
    """
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)

    if df.empty:
        return pd.DataFrame()

    # FIX: Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]
    df = df[[c for c in required if c in df.columns]].copy()
    df.dropna(inplace=True)

    # FIX: Safe tz strip
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert(None)

    return df


def get_fused_data(symbol: str) -> pd.DataFrame:
    """
    Fuses hourly stock data with daily macro factors using merge_asof.
    FIX: Deprecated fillna(method=...) replaced with .ffill().
    """
    stock_df = get_stock_data(symbol, period="1y", interval="1h")

    if stock_df.empty:
        raise ValueError(f"No stock data found for '{symbol}'.")

    start_date = stock_df.index.min().strftime('%Y-%m-%d')
    end_date   = stock_df.index.max().strftime('%Y-%m-%d')

    macro_df = get_macro_data(start_date, end_date)

    stock_df = stock_df.sort_index()

    if macro_df.empty:
        return stock_df.ffill().dropna()

    macro_df = macro_df.sort_index()

    fused_df = pd.merge_asof(
        stock_df,
        macro_df,
        left_index=True,
        right_index=True,
        direction='backward',
    )

    # FIX: Modern ffill API
    fused_df.ffill(inplace=True)
    fused_df.dropna(inplace=True)

    return fused_df


def get_market_news(market: str = "US") -> list:
    """
    Returns market news.
    FIX: Handles both old and new yfinance news formats.
    """
    symbol = "^GSPC" if market == "US" else "RELIANCE.NS"
    try:
        ticker = yf.Ticker(symbol)
        news   = ticker.news or []

        cleaned = []
        for item in news:
            content   = item.get('content', {}) if isinstance(item.get('content'), dict) else {}
            title     = content.get('title') or item.get('title', '')
            link      = (content.get('canonicalUrl', {}).get('url')
                         or item.get('link', '')
                         or item.get('url', ''))
            summary   = content.get('summary') or item.get('summary', '')
            pub_time  = content.get('pubDate') or item.get('providerPublishTime')

            thumb = None
            try:
                res = (content.get('thumbnail', {}).get('resolutions')
                       or item.get('thumbnail', {}).get('resolutions', []))
                if res:
                    thumb = res[0].get('url')
            except Exception:
                pass

            if title and link:
                cleaned.append({
                    "title":     title,
                    "link":      link,
                    "publisher": pub_time,
                    "thumbnail": thumb,
                    "summary":   summary,
                })

        return cleaned[:10]
    except Exception as e:
        print(f"[ERROR] get_market_news: {e}")
        return []
