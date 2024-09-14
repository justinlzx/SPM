from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import EmailStr
from auth.models import get_user_by_email, get_user_by_username
from database import get_db

router = APIRouter()

# Fetch user by email via path parameter
@router.get("/email/{email}")
def get_user_by_email_route(email: EmailStr, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "uuid": user.uuid,
        "email": user.email,
        "username": user.username,
        "role": user.role
    }

# Fetch user by username via path parameter
@router.get("/username/{username}")
def get_user_by_username_route(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "uuid": user.uuid,
        "email": user.email,
        "username": user.username,
        "role": user.role
    }
