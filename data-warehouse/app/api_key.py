# app/api_key.py
import secrets
import sqlite3
from fastapi import HTTPException

DB_PATH = "datawarehouse.db"

# ───────────────────────────────────────────────
# 🔑 API Key Utilities
# ───────────────────────────────────────────────

def generate_api_key() -> str:
    """Generate a secure random 32-character API key."""
    return secrets.token_hex(16)


def get_user_by_api_key(api_key: str):
    """Validate an API key and return basic user info."""
    if not api_key:
        return None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin FROM users WHERE api_key=?", (api_key,))
    row = c.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "username": row[1], "is_admin": bool(row[2])}
    return None


def assign_api_key_to_user(username: str) -> str:
    """Generate a new API key and assign it to a specific user."""
    api_key = generate_api_key()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET api_key=? WHERE username=?", (api_key, username))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    conn.commit()
    conn.close()

    return api_key


def revoke_api_key(username: str):
    """Remove API key for a given user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET api_key=NULL WHERE username=?", (username,))
    conn.commit()
    conn.close()
