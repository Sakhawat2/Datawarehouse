from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter()

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=403, detail="Invalid token")

def require_role(required_role: str):
    def checker(token: str = Depends(get_current_user)):
        if token["role"] != required_role:
            raise HTTPException(status_code=403, detail="Unauthorized")
        return token
    return checker

@router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
def read_admin():
    return {"msg": "Hello, admin!"}
