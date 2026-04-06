"""
JWT-based session management.
Token stored in frontend localStorage, sent as Bearer header.
"""
import jwt, datetime, os

SECRET  = os.getenv("JWT_SECRET", "stockai_secret_key_change_in_production")
ALGO    = "HS256"
EXPIRES = 24  # hours

def create_token(user_id: str, email: str, name: str) -> str:
    payload = {
        "user_id": user_id,
        "email":   email,
        "name":    name,
        "exp":     datetime.datetime.utcnow() + datetime.timedelta(hours=EXPIRES)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise ValueError("Session expired. Please login again.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid session token.")
