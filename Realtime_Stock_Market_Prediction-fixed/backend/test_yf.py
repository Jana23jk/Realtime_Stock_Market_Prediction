import yfinance as yf
import pandas as pd

symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "SBIN.NS"]

print(f"Testing yfinance version: {yf.__version__}")

for sym in symbols:
    print(f"\nDownloading {sym}...")
    try:
        df = yf.download(sym, period="1mo", progress=False)
        if df.empty:
            print(f"❌ {sym}: Empty DataFrame")
        else:
            print(f"✅ {sym}: Found {len(df)} rows. Last close: {df['Close'].iloc[-1]}")
    except Exception as e:
        print(f"❌ {sym}: Error - {e}")
