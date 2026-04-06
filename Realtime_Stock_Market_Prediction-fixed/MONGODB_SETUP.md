# MongoDB Setup Guide

## Step 1 — Install MongoDB

### Windows
1. Download from: https://www.mongodb.com/try/download/community
2. Choose "Windows" → "msi" → Download
3. Run the installer — click Next until done
4. MongoDB installs as a Windows Service (starts automatically)

### Mac
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### Linux (Ubuntu)
```bash
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

## Step 2 — Verify MongoDB is Running
Open a terminal and run:
```bash
mongosh
```
You should see a MongoDB shell prompt. Type `exit` to quit.

## Step 3 — No extra setup needed!
The app auto-creates:
- Database: `stockai`
- Collections: `users`, `watchlists`, `portfolios`
- Indexes on first run

## Step 4 — Run the backend
```bash
cd backend
venv\Scripts\activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## What Gets Stored in MongoDB

### users collection
```json
{
  "name": "Arjun Sharma",
  "email": "arjun@example.com",
  "password": "<sha256 hash>",
  "role": "Premium",
  "created": "2025-03-17T..."
}
```

### watchlists collection
```json
{
  "user_id": "<user_id>",
  "symbols": ["RELIANCE", "TCS", "INFY", "BAJFINANCE"],
  "updated": "2025-03-17T..."
}
```

### portfolios collection
```json
{
  "user_id": "<user_id>",
  "holdings": [
    { "sym": "RELIANCE", "qty": 25, "buy_price": 1280, "added": "2025-03-17T..." },
    { "sym": "TCS",      "qty": 15, "buy_price": 3200, "added": "2025-03-17T..." }
  ]
}
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Connection refused` | MongoDB not running — start it first |
| `Module pymongo not found` | Run `pip install -r requirements.txt` |
| Demo login still works | App falls back to demo mode when DB is offline |

## View Your Data (Optional)
Install MongoDB Compass (free GUI):
https://www.mongodb.com/try/download/compass

Connect to: `mongodb://localhost:27017`
