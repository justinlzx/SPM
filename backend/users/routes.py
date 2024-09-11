from fastapi import APIRouter, Depends, HTTPException
from auth.models import get_user_by_username, get_user_by_email
from database import get_db

router = APIRouter()

# Fetch user by email
@router.get("/email/{email}")
def get_user_by_email_route(email: str, db=Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "uuid": user[0],
        "email": user[1],
        "username": user[2],
        "role": user[4]
    }

# Fetch user by username
@router.get("/username/{username}")
def get_user_by_username_route(username: str, db=Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "uuid": user[0],
        "email": user[1],
        "username": user[2],
        "role": user[4]
    }
