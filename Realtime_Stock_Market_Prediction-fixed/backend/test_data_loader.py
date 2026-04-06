
import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from data.data_loader import get_stock_data

try:
    print("Testing AAPL...")
    df = get_stock_data("AAPL")
    print("AAPL Data:")
    print(df.head())
    print("Columns:", df.columns)
    
    if df.empty:
        print("AAPL dataframe is empty!")
    else:
        print("AAPL fetch successful.")

except Exception as e:
    print(f"Error fetching AAPL: {e}")
    import traceback
    traceback.print_exc()
