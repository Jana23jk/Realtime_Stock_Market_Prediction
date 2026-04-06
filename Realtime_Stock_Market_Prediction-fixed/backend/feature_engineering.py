import pandas as pd
import numpy as np


def create_features(df: pd.DataFrame, external_factors: pd.DataFrame = None) -> pd.DataFrame:
    """
    Computes technical indicators and merges external factors.
    FIX: Division-by-zero guard in CCI calculation.
    FIX: Handles edge cases where rolling windows produce all-NaN columns.
    """
    df = df.copy()
    close = df['Close']

    # 1. Moving Averages
    df['SMA_5']  = close.rolling(window=5).mean()
    df['SMA_10'] = close.rolling(window=10).mean()
    df['SMA_20'] = close.rolling(window=20).mean()

    # 2. RSI (14)
    delta    = close.diff()
    gain     = delta.where(delta > 0, 0.0)
    loss     = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    # FIX: avoid division by zero when avg_loss == 0
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # 3. MACD
    ema_12   = close.ewm(span=12, adjust=False).mean()
    ema_26   = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26

    # 4. EMA (20)
    df['EMA_20'] = close.ewm(span=20, adjust=False).mean()

    # 5. CCI (20) — FIX: guard against zero mean deviation
    tp       = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp   = tp.rolling(window=20).mean()
    mean_dev = (tp - sma_tp).abs().rolling(window=20).mean()
    # Replace zero mean_dev to avoid inf/NaN
    mean_dev_safe = mean_dev.replace(0, np.nan)
    df['CCI_20'] = (tp - sma_tp) / (0.015 * mean_dev_safe)

    # 6. Momentum
    df['Momentum'] = close - close.shift(10)

    # 7. Bollinger Bands
    std_20       = close.rolling(window=20).std()
    df['BB_Mid']   = df['SMA_20']
    df['BB_Upper'] = df['BB_Mid'] + 2 * std_20
    df['BB_Lower'] = df['BB_Mid'] - 2 * std_20

    # 8. Return Features
    df['Return_1'] = close.pct_change(1)
    df['Return_3'] = close.pct_change(3)

    # 9. Merge External Factors
    if external_factors is not None and not external_factors.empty:
        df = df.join(external_factors, how='left')
        df.ffill(inplace=True)

    # Drop NaNs from rolling windows
    df.dropna(inplace=True)

    # 10. Target Labels
    df['Target_Price']  = df['Close'].shift(-1)
    df['target_return'] = df['Close'].pct_change().shift(-1)
    # 1 if next-day close > today * 1.002 (filter out noise)
    df['Target'] = (df['Target_Price'] > df['Close'] * 1.002).astype(int)

    # Drop last row — no next-day target available
    df = df.iloc[:-1].copy()

    return df
