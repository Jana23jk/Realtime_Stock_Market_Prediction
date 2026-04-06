import pandas as pd
import numpy as np

def add_indicators(df):
    df = df.copy()

    # Force Close to be 1-D Series
    close = pd.Series(df["Close"].values.reshape(-1), index=df.index)

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # EMA
    df["ema"] = close.ewm(span=20, adjust=False).mean()

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26

    df = df.dropna().copy()
    return df
