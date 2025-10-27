# app/auth.py
import os
import bcrypt
import datetime
from jose import jwt, JWTError, ExpiredSignatureError  # ✅ Correct import
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import database, models

# ───────────────────────────────────────────────
# 🔐 JWT Configuration
# ───────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ───────────────────────────────────────────────
# 🧩 Password Hashing Utilities
# ───────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash plain password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# ───────────────────────────────────────────────
# 🎟️ JWT Token Handling
# ───────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    """Generate JWT access token"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ───────────────────────────────────────────────
# 👤 Dependency: Get current user from JWT
# ───────────────────────────────────────────────
def get_current_active_user(token: str = Depends(oauth2_scheme)):
    """Decode JWT and return user from DB"""
    db: Session = database.SessionLocal()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    finally:
        db.close()
