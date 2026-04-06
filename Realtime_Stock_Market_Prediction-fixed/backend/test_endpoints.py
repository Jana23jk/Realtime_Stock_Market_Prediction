
import requests
import time

symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
base_url = "http://127.0.0.1:8000/predict?symbol="

for sym in symbols:
    print(f"\n--- Requesting {sym} ---")
    start = time.time()
    try:
        response = requests.get(base_url + sym)
        duration = time.time() - start
        print(f"Status: {response.status_code}, Time: {duration:.2f}s")
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"Error in response: {data['error']}")
            else:
                print(f"Success. Predicted: {data.get('predicted_price')}, Signal: {data.get('signal')}")
        else:
            print(f"HTTP Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
