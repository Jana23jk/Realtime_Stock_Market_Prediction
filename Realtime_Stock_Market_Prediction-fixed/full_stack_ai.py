
import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, request
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import threading

# Initialize Flask App
app = Flask(__name__)

# --- CONSTANTS ---
SEQ_LEN = 60  # Lookback window for LSTM
PREDICT_COL = 'Close'

# --- 1. DATA LOADING & MERGING ---
def fetch_data(symbol):
    """
    Fetches hourly stock data and daily external factors, then merges them.
    External Factors: 
    - Interest Rate (^TNX)
    - Oil Price (CL=F)
    - USD/INR (INR=X)
    """
    print(f"Fetching data for {symbol}...")
    
    # 1. Main Stock Data (Hourly)
    # Note: Yahoo allows max 730 days for hourly data.
    stock = yf.download(symbol, period="1y", interval="1h", progress=False)
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    
    stock = stock[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    
    # 2. External Factors (Daily - will be upsampled)
    # Using small period to ensure coverage, yahoo returns daily for these usually
    start_date = stock.index[0].strftime('%Y-%m-%d')
    end_date = stock.index[-1].strftime('%Y-%m-%d')
    
    tickers = {
        'Interest': '^TNX', 
        'Oil': 'CL=F', 
        'Exchange': 'INR=X'
    }
    
    external_df = pd.DataFrame()
    for name, ticker in tickers.items():
        data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        # We use Close price as the factor value
        external_df[name] = data['Close']
    
    # 3. Merge factors into hourly stock data
    # Remove timezone for clean merge
    stock.index = stock.index.tz_localize(None)
    external_df.index = external_df.index.tz_localize(None)
    
    # Merge using 'asof' (backward fill) to align daily macro data with hourly stock data
    merged = pd.merge_asof(
        stock.sort_index(), 
        external_df.sort_index(), 
        left_index=True, 
        right_index=True, 
        direction='backward'
    )
    
    # 4. Simulated News Sentiment (Random for demo, typically requires NLP API)
    # In a real academic project, you'd fetch headlines and derive this score.
    np.random.seed(42)
    merged['Sentiment'] = np.random.uniform(-1, 1, size=len(merged))
    
    # Fill remaining NaNs (e.g., weekends/holidays in macro data)
    merged = merged.fillna(method='ffill').fillna(method='bfill')
    
    return merged

# --- 2. PREPROCESSING ---
def preprocess_data(df):
    """
    Normalizes data and creates sequences for LSTM.
    """
    # Normalize features
    scaler = MinMaxScaler()
    feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Interest', 'Oil', 'Exchange', 'Sentiment']
    
    # Ensure all columns exist
    df = df[feature_cols]
    
    scaled_data = scaler.fit_transform(df.values)
    
    X, y = [], []
    target_idx = feature_cols.index(PREDICT_COL)
    
    for i in range(SEQ_LEN, len(scaled_data)):
        X.append(scaled_data[i-SEQ_LEN:i])
        y.append(scaled_data[i, target_idx])
        
    return np.array(X), np.array(y), scaler, scaled_data, target_idx

# --- 3. LSTM MODEL ---
def build_lstm_model(input_shape):
    """
    Builds a simple LSTM model.
    """
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=input_shape),
        LSTM(units=50, return_sequences=False),
        Dense(units=25),
        Dense(units=1) # Predicted Price
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# --- 4. FLASK API ENDPOINT ---
@app.route('/predict', methods=['GET'])
def predict_stock():
    try:
        symbol = request.args.get('symbol', 'AAPL')
        
        # A. Pipeline Execution
        df = fetch_data(symbol)
        X, y, scaler, scaled_full, target_idx = preprocess_data(df)
        
        # B. Train Model (Simplified for Demo: Retrains on request)
        # In production, load a pre-trained model.
        model = build_lstm_model((X.shape[1], X.shape[2]))
        
        # Train on last 500 points for speed
        print("Training model...")
        history = model.fit(X[-500:], y[-500:], batch_size=32, epochs=5, verbose=0)
        loss = history.history['loss'][-1]
        
        # C. Predict Next Hour
        last_sequence = scaled_full[-SEQ_LEN:].reshape(1, SEQ_LEN, X.shape[2])
        prediction_scaled = model.predict(last_sequence)[0][0]
        
        # D. Inverse Scaling
        # Create dummy array to inverse transform
        dummy = np.zeros((1, X.shape[2]))
        dummy[0, target_idx] = prediction_scaled
        predicted_price = scaler.inverse_transform(dummy)[0, target_idx]
        
        current_price = df['Close'].iloc[-1]
        
        # E. Determine Direction
        direction = "Bullish" if predicted_price > current_price else "Bearish"
        
        return jsonify({
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "last_price": float(round(current_price, 2)),
            "predicted_next_hour": float(round(predicted_price, 2)),
            "direction": direction,
            "training_loss": float(round(loss, 6))
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting Multi-Factor AI Stock System...")
    app.run(port=5000, debug=True, use_reloader=False)
