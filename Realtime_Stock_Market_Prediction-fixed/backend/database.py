"""
MongoDB database layer.
Collections:
  users      — { email, password_hash, name, created_at }
  watchlists — { user_id, symbols: [...] }
  portfolios — { user_id, holdings: [{ sym, qty, buy_price, added_at }] }
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os, datetime

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "stockai"

_client = None
_db     = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db     = _client[DB_NAME]
        # Indexes
        _db.users.create_index("email", unique=True)
        _db.watchlists.create_index("user_id")
        _db.portfolios.create_index("user_id")
    return _db

# ── Users ──────────────────────────────────────────────────

def create_user(name: str, email: str, password: str) -> dict:
    db = get_db()
    if db.users.find_one({"email": email}):
        raise ValueError("Email already registered.")
    doc = {
        "name":     name,
        "email":    email,
        "password": password,
        "role":     "Premium",
        "created":  datetime.datetime.utcnow().isoformat()
    }
    result = db.users.insert_one(doc)
    return {"id": str(result.inserted_id), "name": name, "email": email, "role": "Premium"}

def login_user(email: str, password: str) -> dict:
    db   = get_db()
    user = db.users.find_one({"email": email, "password": password})
    if not user:
        raise ValueError("Invalid email or password.")

    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user.get("role","Premium")}

def reset_password(email: str, new_password: str) -> bool:
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        raise ValueError("User with this email not found.")
    db.users.update_one({"email": email}, {"$set": {"password": new_password}})
    return True

# ── Watchlist ──────────────────────────────────────────────

def get_watchlist(user_id: str) -> list:
    db  = get_db()
    doc = db.watchlists.find_one({"user_id": user_id})
    return doc["symbols"] if doc else ["RELIANCE","TCS","INFY","HDFCBANK","SBIN"]

def set_watchlist(user_id: str, symbols: list) -> list:
    db = get_db()
    db.watchlists.update_one(
        {"user_id": user_id},
        {"$set": {"symbols": symbols, "updated": datetime.datetime.utcnow().isoformat()}},
        upsert=True
    )
    return symbols

# ── Portfolio ──────────────────────────────────────────────

def get_portfolio(user_id: str) -> list:
    db  = get_db()
    doc = db.portfolios.find_one({"user_id": user_id})
    return doc["holdings"] if doc else []

def add_holding(user_id: str, sym: str, qty: float, buy_price: float) -> list:
    db = get_db()
    doc = db.portfolios.find_one({"user_id": user_id})
    holdings = doc["holdings"] if doc else []

    # Update if exists
    found = False
    for h in holdings:
        if h["sym"] == sym:
            # Weighted average buy price
            total_qty = h["qty"] + qty
            h["buy_price"] = round((h["buy_price"]*h["qty"] + buy_price*qty) / total_qty, 2)
            h["qty"] = total_qty
            found = True; break

    if not found:
        holdings.append({
            "sym":       sym,
            "qty":       qty,
            "buy_price": buy_price,
            "added":     datetime.datetime.utcnow().isoformat()
        })

    db.portfolios.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated": datetime.datetime.utcnow().isoformat()}},
        upsert=True
    )
    return holdings

def remove_holding(user_id: str, sym: str) -> list:
    db = get_db()
    doc = db.portfolios.find_one({"user_id": user_id})
    if not doc:
        return []
    holdings = [h for h in doc["holdings"] if h["sym"] != sym]
    db.portfolios.update_one({"user_id": user_id}, {"$set": {"holdings": holdings}})
    return holdings

def update_holding(user_id: str, sym: str, qty: float, buy_price: float) -> list:
    db = get_db()
    doc = db.portfolios.find_one({"user_id": user_id})
    holdings = doc["holdings"] if doc else []
    for h in holdings:
        if h["sym"] == sym:
            h["qty"]       = qty
            h["buy_price"] = buy_price
            break
    db.portfolios.update_one({"user_id": user_id}, {"$set": {"holdings": holdings}})
    return holdings
