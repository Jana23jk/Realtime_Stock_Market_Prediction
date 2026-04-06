import yfinance as yf
import pandas as pd
import numpy as np

print("Downloading...")
df = yf.download("AAPL", period="1mo", progress=False)
print("Original Columns:", df.columns)

if isinstance(df.columns, pd.MultiIndex):
    print("Detected MultiIndex. Flattening...")
    df.columns = df.columns.get_level_values(0)

print("New Columns:", df.columns)
print("Type of df['Close']:", type(df['Close']))

last_val = df['Close'].iloc[-1]
print(f"Last value: {last_val} (Type: {type(last_val)})")

try:
    f_val = float(last_val)
    print("Float conversion success:", f_val)
except:
    print("Float conversion failed")
