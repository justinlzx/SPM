from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import EmailStr
from auth.models import create_user, get_user_by_username, get_user_by_email
from database import get_db
from auth.utils import hash_password, verify_password, generate_uuid

router = APIRouter()

@router.post("/register")
def register(
    email: EmailStr = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db=Depends(get_db)
):
    if get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Generate UUID
    user_uuid = generate_uuid()
    hashed_password = hash_password(password, user_uuid)

    create_user(db, user_uuid, email, username, hashed_password, role)
    return {"message": "User registered successfully", "uuid": user_uuid}

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    user = get_user_by_username(db, username)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    user_uuid = user[0]  # UUID is the first item in the row fetched by get_user_by_username
    stored_hash = user[3]  # Assuming that user[3] is the stored hashed password
    
    if not verify_password(password, stored_hash, user_uuid):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    return {"message": "Login successful"}
