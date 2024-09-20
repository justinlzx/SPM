from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ..auth.models import create_user, get_user_by_email, get_user_by_staff_id
from ..auth.utils import generate_JWT, hash_password, verify_password
from ..database import get_db

router = APIRouter()


@router.post("/register")
def register(
    staff_id: int = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check if staff_id or email already exists
    if get_user_by_staff_id(db, staff_id):
        raise HTTPException(status_code=400, detail="Staff ID already exists")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password using staff_id as salt
    hashed_password = hash_password(password, str(staff_id))

    # Create the user in the database
    create_user(db, staff_id, email, hashed_password)
    return {"message": "User registered successfully", "staff_id": staff_id}


@router.post("/login")
def login(
    staff_id: int = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    user = get_user_by_staff_id(db, staff_id)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid staff ID or password")

    stored_hash = user.hashed_password

    if not verify_password(password, stored_hash, str(staff_id)):
        raise HTTPException(status_code=400, detail="Invalid staff ID or password")

    access_token = generate_JWT({"user_id": staff_id})

    return {
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "staff_id": staff_id,
        },
    }
