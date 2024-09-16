from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from .models import create_user, get_user_by_username, get_user_by_email
from ..database import get_db
from .utils import hash_password, verify_password, generate_uuid
from pydantic import EmailStr

router = APIRouter()

@router.post("/register")
def register(
    email: EmailStr = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if username or email already exists
    if get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Generate UUID and hash the password
    user_uuid = generate_uuid()
    hashed_password = hash_password(password, user_uuid)

    # Create the user in the database
    create_user(db, user_uuid, email, username, hashed_password, role)
    return {"message": "User registered successfully", "uuid": user_uuid}

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_username(db, username)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    user_uuid = user.uuid
    stored_hash = user.hashed_password
    
    if not verify_password(password, stored_hash, user_uuid):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    return {"message": "Login successful"}
