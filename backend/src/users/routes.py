from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ..auth.models import get_user_by_email
from ..database import get_db

router = APIRouter()


# Fetch user by email via path parameter
@router.get("/email/{email}")
def get_user_by_email_route(email: EmailStr, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"email": user.email}
