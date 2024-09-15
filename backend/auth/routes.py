from auth.models import create_user, get_user_by_email, get_user_by_username
from auth.utils import generate_uuid, hash_password, verify_password
from database import get_db
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/register")
def register(
    email: EmailStr = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
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
    username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    user = get_user_by_username(db, username)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    user_uuid = user.uuid
    stored_hash = user.hashed_password

    if not verify_password(password, stored_hash, user_uuid):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    return {"message": "Login successful"}
