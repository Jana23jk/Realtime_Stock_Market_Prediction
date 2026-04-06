import yfinance as yf
import pandas as pd

try:
    print("Downloading data...")
    df = yf.download("AAPL", period="1mo", progress=False)
    print("\nColumns:", df.columns)
    
    if "Close" in df.columns:
        print("Close column found.")
        print("Type of df['Close']:", type(df['Close']))
        print("Type of df['Close'].iloc[-1]:", type(df['Close'].iloc[-1]))
        
        try:
            val = float(df['Close'].iloc[-1])
            print("Float conversion success:", val)
        except Exception as e:
            print("Float conversion failed:", e)
    else:
        print("Close column NOT found in top level.")

except Exception as e:
    print("General Error:", e)
