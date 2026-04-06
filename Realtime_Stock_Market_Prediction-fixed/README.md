# 📈 Real-time Stock Market Prediction

AI-powered stock direction predictor using XGBoost, sentiment analysis, and live yfinance data.

---

## 🚀 Quick Start

### 1. Backend (FastAPI)

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (one-time)
python -c "import nltk; nltk.download('vader_lexicon')"

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be live at: http://127.0.0.1:8000

### 2. Frontend (React + Vite)

```bash
cd frontend

# Copy env file
cp .env.example .env
# Edit .env if your backend runs on a different URL

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be live at: http://localhost:5173

---

## ⚙️ How It Works

1. **Data**: yfinance downloads 3 years of OHLCV + macro data (S&P 500, Gold, Oil, USD/INR)
2. **Features**: SMA, EMA, RSI, MACD, Bollinger Bands, CCI, Momentum + macro factors
3. **Model**: XGBoost with TimeSeriesSplit cross-validation + SelectKBest feature selection
4. **Sentiment**: VADER NLP on latest news headlines from yfinance
5. **Output**: UP/DOWN direction + confidence + projected price + model metrics

---

## 📊 Supported Stocks

| Market | Examples |
|--------|----------|
| 🇺🇸 US | AAPL, MSFT, GOOGL, TSLA, NVDA, AMZN, META |
| 🇮🇳 India | TCS.NS, RELIANCE.NS, INFY.NS, HDFCBANK.NS |

> **Tip**: For Indian stocks, you can type `TCS` in the search bar — the `.NS` suffix is added automatically.

---

## 🐛 Bugs Fixed (v2)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `requirements.txt` | Missing `xgboost`, `nltk`, `scipy` | Added |
| 2 | `data_loader.py` | `tz_localize(None)` crash on naive index | Use `tz_convert(None)` |
| 3 | `data_loader.py` | Deprecated `fillna(method=...)` | Use `.ffill()` / `.bfill()` |
| 4 | `feature_engineering.py` | CCI division by zero → `inf` values | Guard with `.replace(0, np.nan)` |
| 5 | `model_training.py` | `scale_pos_weight` crash if single class | Added class count guard |
| 6 | `app.py` | Indian `.NS` suffix only for TCS/RELIANCE | `resolve_symbol()` for all stocks |
| 7 | `app.py` `/news` | Old yfinance news schema | Handle both formats |
| 8 | `inference/predictor.py` | `scaler.data_min_` doesn't exist | Use `inverse_transform()` |
| 9 | `data/macro_loader.py` | Same tz + ffill bugs | Fixed |
| 10 | `App.jsx` | Infinite re-fetch loop (`useEffect` deps) | `fetchedRef` sentinel pattern |
| 11 | `App.jsx` | Hardcoded `127.0.0.1:8000` | `VITE_API_URL` env variable |
| 12 | `App.jsx` | No loading state during 30-60s model training | Skeleton + status messages |
| 13 | `App.jsx` | No error recovery | Per-stock Retry button |
| 14 | `index.css` | Vite default `#root` CSS breaks layout | Proper reset |
| 15 | `App.css` | Conflicting `text-align: center` on `#root` | Cleared |

---

## 📁 Project Structure

```
├── backend/
│   ├── app.py                  # FastAPI server (main entry point)
│   ├── data_loader.py          # Stock + macro data fetching
│   ├── feature_engineering.py  # Technical indicators
│   ├── model_training.py       # XGBoost training pipeline
│   ├── sentiment_module.py     # VADER news sentiment
│   ├── evaluation.py           # Metrics calculation
│   ├── requirements.txt        # Python dependencies
│   ├── data/
│   │   ├── data_loader.py      # Hourly fused data loader
│   │   └── macro_loader.py     # Macro factor fetcher
│   └── inference/
│       ├── predictor.py        # LSTM-style price predictor
│       └── sentiment.py        # Advanced sentiment module
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main React component
    │   ├── index.css           # All styles
    │   └── main.jsx            # React entry point
    ├── .env.example            # Environment variable template
    └── package.json
```

---

## ❗ Important Notes

- **First prediction takes 30–90 seconds** — the model trains fresh on 3 years of data. Subsequent requests use a 6-hour cache.
- **yfinance rate limits**: Avoid fetching too many stocks simultaneously. The app fetches predictions sequentially for this reason.
- **Not financial advice**: This is an academic/ML project. Do not use for real trading decisions.
