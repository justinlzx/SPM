from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import EmailStr
from ..auth.models import get_user_by_email, get_user_by_staff_id
from ..database import get_db

router = APIRouter()


# Fetch user by email via path parameter
@router.get("/email/{email}")
def get_user_by_email_route(email: EmailStr, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"staff_id": user.staff_id, "email": user.email}


# Fetch user by staff ID via path parameter
@router.get("/staff_id/{staff_id}")
def get_user_by_staff_id_route(staff_id: int, db: Session = Depends(get_db)):
    user = get_user_by_staff_id(db, staff_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"staff_id": user.staff_id, "email": user.email}
