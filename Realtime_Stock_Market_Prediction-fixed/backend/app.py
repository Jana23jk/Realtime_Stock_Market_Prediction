import time
import traceback

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Database & Auth
try:
    from database import (
        create_user, login_user, reset_password,
        get_watchlist, set_watchlist,
        get_portfolio, add_holding, remove_holding, update_holding
    )
    from auth import create_token, verify_token
    DB_AVAILABLE = True
except Exception as _db_err:
    print(f"[WARN] MongoDB not available: {_db_err}. Running without DB.")
    DB_AVAILABLE = False

from data_loader import load_stock_data, load_external_factors
from feature_engineering import create_features
from sentiment_module import SentimentAnalyzer
from model_training import train_and_select_model
from evaluation import evaluate_model, get_feature_importances

# ── Request / Response Models ──────────────────────────────
class RegisterReq(BaseModel):
    name:     str
    email:    str
    password: str

class LoginReq(BaseModel):
    email:    str
    password: str

class ResetPasswordReq(BaseModel):
    email: str
    new_password: str

class WatchlistReq(BaseModel):
    symbols: List[str]

class HoldingReq(BaseModel):
    sym:       str
    qty:       float
    buy_price: float

class UpdateHoldingReq(BaseModel):
    qty:       float
    buy_price: float

def get_user(authorization: Optional[str] = None) -> dict:
    """Extract & verify JWT from Authorization header."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization.split(" ", 1)[1]
    try:
        return verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

app = FastAPI(title="Hybrid Stock Direction Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sentiment_engine = SentimentAnalyzer()
MODEL_CACHE: dict = {}
CACHE_TTL = 21600  # 6 hours


def resolve_yf_symbol(raw: str) -> str:
    """
    Convert a user-entered symbol to a valid yfinance ticker.
    Handles: Indian stocks (.NS), common indices, spaces in names.

    Examples:
      RELIANCE    -> RELIANCE.NS
      TCS         -> TCS.NS
      TCS.NS      -> TCS.NS
      NIFTY 50    -> ^NSEI
      NIFTY50     -> ^NSEI
      SENSEX      -> ^BSESN
      BANKNIFTY   -> ^NSEBANK
      AAPL        -> AAPL
      S&P 500     -> ^GSPC
    """
    s = raw.upper().strip()

    # Common index aliases — check BEFORE anything else
    INDEX_MAP = {
        'NIFTY 50':   '^NSEI',   'NIFTY50':    '^NSEI',   'NIFTY':      '^NSEI',
        'SENSEX':     '^BSESN',  'BSE SENSEX': '^BSESN',  'BSE':        '^BSESN',
        'BANKNIFTY':  '^NSEBANK','BANK NIFTY': '^NSEBANK',
        'NIFTYMIDCAP':'^CNXMIDCAP',
        'S&P 500':    '^GSPC',   'S&P500':     '^GSPC',   'SPX':        '^GSPC',
        'DOW':        '^DJI',    'DOW JONES':  '^DJI',    'DJIA':       '^DJI',
        'NASDAQ':     '^IXIC',   'NASDAQ 100': '^NDX',    'NDX':        '^NDX',
        'VIX':        '^VIX',    'INDIA VIX':  '^INDIAVIX',
    }
    if s in INDEX_MAP:
        return INDEX_MAP[s]

    # Already has an exchange suffix (.NS, .BO, ^) → return as-is
    if s.startswith('^') or '.' in s:
        return s

    # Known NSE-listed stocks
    INDIAN_STOCKS = {
        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'SBIN', 'ICICIBANK',
        'WIPRO', 'HINDUNILVR', 'ADANIENT', 'ADANIPORTS', 'AXISBANK',
        'BAJFINANCE', 'BAJAJFINSV', 'BHARTIARTL', 'BPCL', 'CIPLA',
        'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM',
        'HCLTECH', 'HDFC', 'HEROMOTOCO', 'HINDALCO', 'ITC', 'JSWSTEEL',
        'KOTAKBANK', 'LT', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC',
        'ONGC', 'POWERGRID', 'SUNPHARMA', 'TATAMOTORS', 'TATASTEEL',
        'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'VEDL', 'ZOMATO',
        'PAYTM', 'NYKAA', 'DMART', 'AVENUE', 'POLICYBZR', 'IRCTC',
        'PIDILITIND', 'DABUR', 'MARICO', 'COLPAL', 'BRITANNIA',
        'ASIANPAINT', 'BERGEPAINT', 'HAVELLS', 'VOLTAS', 'WHIRLPOOL',
        'HDFCLIFE', 'SBILIFE', 'ICICIGI', 'LICI', 'STARHEALTH',
        'BAJAJ-AUTO', 'ASHOKLEY', 'TVSMOTOR', 'BALKRISIND',
    }
    if s in INDIAN_STOCKS:
        return s + '.NS'

    return s


def get_or_train_model(raw_symbol: str):
    """
    FIX 1: Always resolve symbol before fetching — never pass bare 'RELIANCE' to yfinance.
    FIX 2: Cache key uses resolved symbol so RELIANCE and RELIANCE.NS share the same cache entry.
    """
    yf_symbol = resolve_yf_symbol(raw_symbol)
    cache_key  = yf_symbol

    if cache_key in MODEL_CACHE:
        cached = MODEL_CACHE[cache_key]
        if time.time() - cached['timestamp'] < CACHE_TTL:
            print(f"[CACHE HIT] {cache_key}")
            return cached

    print(f"\n[TRAIN] Fetching data for {yf_symbol} ...")
    df_stock = load_stock_data(yf_symbol, period="3y")
    if df_stock is None or df_stock.empty:
        raise ValueError(
            f"No price data for '{yf_symbol}'. "
            "Check the symbol (e.g. use RELIANCE.NS for NSE, AAPL for NASDAQ)."
        )

    df_macro = load_external_factors(period="3y")

    df_features = create_features(df_stock, df_macro if not df_macro.empty else None)

    if df_features.empty or len(df_features) < 60:
        raise ValueError(
            f"Not enough historical data for '{yf_symbol}' after feature engineering "
            f"(got {len(df_features)} rows, need ≥ 60)."
        )

    # Neutral sentiment placeholders for training; real sentiment used at inference
    df_features['Sentiment_Score'] = 0.0
    df_features['Pos_Neg_Ratio']   = 1.0
    df_features['News_Count']      = 0

    best_model, scaler, feature_names, models_dict = train_and_select_model(df_features)

    # Walk-forward evaluation on last 20%
    drop_cols  = ['Target', 'Target_Price', 'Date', 'target_return']
    all_feats  = [c for c in df_features.columns if c not in drop_cols]
    X          = df_features[all_feats]
    y          = df_features['Target']
    split_idx  = int(len(X) * 0.8)
    X_test     = X.iloc[split_idx:][feature_names]
    y_test     = y.iloc[split_idx:]
    X_test_sc  = scaler.transform(X_test)
    metrics, cm = evaluate_model(best_model, X_test_sc, y_test)
    f_imp       = get_feature_importances(best_model, feature_names)

    record = {
        'model':              best_model,
        'reg_model':          models_dict.get('Regressor'),
        'scaler':             scaler,
        'features':           feature_names,
        'metrics':            metrics,
        'confusion_matrix':   cm,
        'feature_importance': f_imp,
        'latest_df':          df_features.iloc[-1:].copy(),
        'timestamp':          time.time(),
        'yf_symbol':          yf_symbol,
    }
    MODEL_CACHE[cache_key] = record
    return record


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}


# ── Predict ────────────────────────────────────────────────────────────────

@app.get("/predict")
def predict_stock(stock: str = Query(..., description="e.g. AAPL or RELIANCE or TCS.NS")):
    """
    Main AI prediction endpoint.
    Returns direction (UP/DOWN), confidence, projected price, metrics, sentiment.
    """
    try:
        model_data = get_or_train_model(stock)
        yf_sym     = model_data['yf_symbol']

        # Live sentiment using the resolved yf symbol
        s_data = sentiment_engine.get_todays_sentiment(yf_sym)

        latest_row = model_data['latest_df'].copy()

        # Inject today's real sentiment into the inference row
        for col, val in [
            ('Sentiment_Score', s_data['Sentiment_Score']),
            ('Pos_Neg_Ratio',   s_data['Pos_Neg_Ratio']),
            ('News_Count',      s_data['News_Count']),
        ]:
            latest_row[col] = val

        features = model_data['features']

        # Safety: ensure every required feature column exists
        for f in features:
            if f not in latest_row.columns:
                latest_row[f] = 0.0

        X_today        = latest_row[features]
        X_today_scaled = model_data['scaler'].transform(X_today)

        model     = model_data['model']
        reg_model = model_data['reg_model']

        pred_class = int(model.predict(X_today_scaled)[0])
        pred_prob  = float(model.predict_proba(X_today_scaled)[0][1])

        # FIX: Fetch live price for predicted_price base.
        # Using latest_df['Close'] (stale training price) caused massive % errors.
        pred_price = None
        live_price = None
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(yf_sym)
            fi = ticker_obj.fast_info
            live_price = fi.get('last_price') or fi.get('lastPrice')
            if not live_price:
                df_tmp = ticker_obj.history(period="2d")
                if not df_tmp.empty:
                    live_price = float(df_tmp['Close'].iloc[-1])
        except Exception:
            pass
        # Fallback to training close if live unavailable
        if not live_price:
            live_price = float(latest_row['Close'].values[0])

        if reg_model is not None:
            try:
                pred_return = float(np.clip(reg_model.predict(X_today_scaled)[0], -0.05, 0.05))
                pred_price  = round(float(live_price) * (1 + pred_return), 2)
            except Exception:
                pred_price = None

        direction  = "UP" if pred_class == 1 else "DOWN"
        confidence = round(pred_prob, 4)
        metrics    = model_data['metrics']

        roc_val = metrics.get('ROC_AUC', 0)
        roc_out = round(float(roc_val), 4) if isinstance(roc_val, (int, float)) else 0.0

        return {
            "prediction":      direction,
            "predicted_price": pred_price if pred_price is not None else "N/A",
            "current_price":   round(float(live_price), 2) if live_price else None,
            "confidence":      confidence,
            "stock":           stock,
            "resolved_symbol": yf_sym,
            "metrics": {
                "accuracy":  round(float(metrics.get('Accuracy',  0)), 4),
                "precision": round(float(metrics.get('Precision', 0)), 4),
                "recall":    round(float(metrics.get('Recall',    0)), 4),
                "f1_score":  round(float(metrics.get('F1_score',  0)), 4),
                "roc_auc":   roc_out,
            },
            "sentiment": {
                "score": round(s_data['Sentiment_Score'], 4),
                "ratio": round(s_data['Pos_Neg_Ratio'],   4),
                "count": s_data['News_Count'],
            },
            "feature_importance": model_data['feature_importance'][:5],
        }

    except ValueError as ve:
        print(f"[PREDICT ERROR] {ve}")
        return {"error": str(ve)}
    except Exception:
        traceback.print_exc()
        return {"error": "Model training/inference failed. Check backend terminal for details."}


# ── Quote ──────────────────────────────────────────────────────────────────

@app.get("/quote")
def get_quote(symbol: str):
    """Fast current-price fetch with 3-strategy fallback."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        price  = None

        try:
            fi = ticker.fast_info
            price = fi.get('last_price') or fi.get('lastPrice')
        except Exception:
            pass

        if not price:
            try:
                df = ticker.history(period="5d")
                if not df.empty:
                    price = float(df['Close'].iloc[-1])
            except Exception:
                pass

        if not price:
            df = yf.download(symbol, period="5d", progress=False, auto_adjust=True)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                price = float(df['Close'].iloc[-1])

        if not price:
            return {"error": f"Could not fetch price for {symbol}"}

        return {"symbol": symbol, "current_price": round(float(price), 2), "timestamp": time.time()}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


# ── History ────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(symbol: str, period: str = "1y"):
    """
    Returns OHLCV history for charting.
    period: 1d (intraday 5-min), 5d (hourly), 1mo (daily), 1y (daily last 100 days)
    """
    import yfinance as yf
    try:
        # Map frontend period labels to yfinance params
        period_map = {
            "1d":  ("1d",  "5m"),    # today, 5-min intervals
            "5d":  ("5d",  "1h"),    # 5 days, hourly
            "1mo": ("1mo", "1d"),    # 1 month, daily
            "1y":  ("1y",  "1d"),    # 1 year, daily
        }
        yf_period, interval = period_map.get(period, ("1y", "1d"))

        df = yf.download(symbol, period=yf_period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return []
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)

        result = []
        for idx, row in df.iterrows():
            try:
                # For intraday, show time; for daily show date
                if interval in ("5m", "1h"):
                    label = str(idx.strftime("%H:%M") if hasattr(idx, 'strftime') else idx)
                else:
                    label = str(idx).split()[0]
                result.append({"date": label, "price": round(float(row['Close']), 2)})
            except Exception:
                continue
        return result
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


# ── News ───────────────────────────────────────────────────────────────────

@app.get("/news")
def get_news(market: str = "US"):
    """Market news — handles both old and new yfinance news schemas."""
    import yfinance as yf
    symbol = "^GSPC" if market == "US" else "RELIANCE.NS"
    try:
        ticker = yf.Ticker(symbol)
        news   = ticker.news or []
        result = []
        for item in news[:10]:
            try:
                content   = item.get('content', {}) if isinstance(item.get('content'), dict) else {}
                title     = content.get('title') or item.get('title', '')
                link      = (content.get('canonicalUrl', {}).get('url')
                             or item.get('link', '') or item.get('url', ''))
                summary   = content.get('summary') or item.get('summary', '')
                pub_time  = content.get('pubDate') or item.get('providerPublishTime') or int(time.time())
                thumbnail = ''
                try:
                    res = (content.get('thumbnail', {}).get('resolutions')
                           or item.get('thumbnail', {}).get('resolutions', []))
                    if res:
                        thumbnail = res[0].get('url', '')
                except Exception:
                    pass
                if title:
                    result.append({"title": title, "summary": summary, "link": link,
                                   "publisher": pub_time, "thumbnail": thumbnail})
            except Exception:
                continue
        return result
    except Exception as e:
        print(f"[NEWS ERROR] {e}")
        return []


# ── Debug (dev only) ───────────────────────────────────────────────────────

@app.get("/debug/predict")
def debug_predict(stock: str):
    """
    Same as /predict but returns the full traceback in the response.
    Use this to diagnose prediction failures directly in the browser.
    Example: http://127.0.0.1:8000/debug/predict?stock=RELIANCE
    """
    import io, sys
    buf = io.StringIO()
    old_stderr = sys.stderr
    sys.stderr = buf
    try:
        result = predict_stock(stock)
        sys.stderr = old_stderr
        return {**result, "_debug_log": buf.getvalue()}
    except Exception as e:
        sys.stderr = old_stderr
        return {
            "error": str(e),
            "_traceback": traceback.format_exc(),
            "_debug_log": buf.getvalue(),
        }


# ══════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.post("/auth/register")
def register(req: RegisterReq):
    """Register a new user."""
    if not DB_AVAILABLE:
        return {"error": "Database not available. Start MongoDB first."}
    try:
        user  = create_user(req.name.strip(), req.email.strip().lower(), req.password)
        token = create_token(user["id"], user["email"], user["name"])
        return {"token": token, "user": user}
    except ValueError as e:
        return {"error": str(e)}
    except Exception:
        traceback.print_exc()
        return {"error": "Registration failed."}


@app.post("/auth/login")
def login(req: LoginReq):
    """Login and receive JWT token."""
    if not DB_AVAILABLE:
        # Demo fallback when MongoDB is offline
        if req.email == "demo@stockai.in" and req.password == "demo123":
            demo_user = {"id": "demo", "name": "Demo User", "email": req.email, "role": "Premium"}
            import auth
            token = auth.create_token("demo", req.email, "Demo User")
            return {"token": token, "user": demo_user}
        return {"error": "Database not available. Start MongoDB first."}
    try:
        user  = login_user(req.email.strip().lower(), req.password)
        token = create_token(user["id"], user["email"], user["name"])
        return {"token": token, "user": user}
    except ValueError as e:
        return {"error": str(e)}
    except Exception:
        traceback.print_exc()
        return {"error": "Login failed."}


@app.post("/auth/reset-password")
def reset_password_endpoint(req: ResetPasswordReq):
    """Reset user password directly."""
    if not DB_AVAILABLE:
        return {"error": "Database not available. Start MongoDB first."}
    try:
        reset_password(req.email.strip().lower(), req.new_password)
        return {"message": "Password reset successfully."}
    except ValueError as e:
        return {"error": str(e)}
    except Exception:
        traceback.print_exc()
        return {"error": "Password reset failed."}

@app.get("/auth/me")
def get_me(authorization: Optional[str] = Header(None)):
    """Validate token and return user info."""
    user = get_user(authorization)
    return {"user_id": user["user_id"], "name": user["name"], "email": user["email"]}


# ══════════════════════════════════════════════════════════
# WATCHLIST ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/watchlist")
def fetch_watchlist(authorization: Optional[str] = Header(None)):
    """Get user's saved watchlist."""
    user = get_user(authorization)
    try:
        return {"symbols": get_watchlist(user["user_id"])}
    except Exception:
        traceback.print_exc()
        return {"symbols": ["RELIANCE","TCS","INFY","HDFCBANK","SBIN"]}


@app.post("/watchlist")
def save_watchlist(req: WatchlistReq, authorization: Optional[str] = Header(None)):
    """Save user's watchlist."""
    user = get_user(authorization)
    # Validate: max 20 symbols, uppercase
    symbols = [s.upper().strip() for s in req.symbols if s.strip()][:20]
    try:
        return {"symbols": set_watchlist(user["user_id"], symbols)}
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to save watchlist."}


# ══════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/portfolio")
def fetch_portfolio(authorization: Optional[str] = Header(None)):
    """Get user's portfolio holdings."""
    user = get_user(authorization)
    try:
        return {"holdings": get_portfolio(user["user_id"])}
    except Exception:
        traceback.print_exc()
        return {"holdings": []}


@app.post("/portfolio/add")
def add_to_portfolio(req: HoldingReq, authorization: Optional[str] = Header(None)):
    """Add or update a holding."""
    user = get_user(authorization)
    if req.qty <= 0 or req.buy_price <= 0:
        return {"error": "Quantity and buy price must be greater than 0."}
    try:
        holdings = add_holding(
            user["user_id"],
            req.sym.upper().strip(),
            req.qty,
            req.buy_price
        )
        return {"holdings": holdings, "message": f"{req.sym.upper()} added to portfolio."}
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to add holding."}


@app.put("/portfolio/{sym}")
def update_portfolio_holding(
    sym: str,
    req: UpdateHoldingReq,
    authorization: Optional[str] = Header(None)
):
    """Update qty and buy price of an existing holding."""
    user = get_user(authorization)
    if req.qty <= 0 or req.buy_price <= 0:
        return {"error": "Quantity and buy price must be greater than 0."}
    try:
        holdings = update_holding(user["user_id"], sym.upper(), req.qty, req.buy_price)
        return {"holdings": holdings, "message": f"{sym.upper()} updated."}
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to update holding."}


@app.delete("/portfolio/{sym}")
def delete_portfolio_holding(sym: str, authorization: Optional[str] = Header(None)):
    """Remove a stock from portfolio."""
    user = get_user(authorization)
    try:
        holdings = remove_holding(user["user_id"], sym.upper())
        return {"holdings": holdings, "message": f"{sym.upper()} removed from portfolio."}
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to remove holding."}
