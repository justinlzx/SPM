from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ..auth.models import create_user, get_user_by_email
from ..auth.utils import generate_JWT, hash_password, verify_password
from ..database import get_db

router = APIRouter()

@router.post("/register")
def register(
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check if email already exists
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password (no need for staff_id as salt anymore, can use email as salt)
    hashed_password = hash_password(password, email)

    # Create the user in the database
    create_user(db, email, hashed_password)
    return {"message": "User registered successfully", "email": email}

@router.post("/login")
def login(
    email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    stored_hash = user.hashed_password

    if not verify_password(password, stored_hash, email):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = generate_JWT({"user_email": email})

    return {
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "email": email,
        },
    }