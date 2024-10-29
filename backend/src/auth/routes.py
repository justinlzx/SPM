from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.models import Auth, get_user_by_email
from ..auth.utils import generate_JWT, verify_password
from ..database import get_db
from ..employees.models import Employee

router = APIRouter()


# Update the get_user_by_email function
def get_user_by_email(db: Session, email: str):
    return db.query(Auth).filter(func.lower(Auth.email) == func.lower(email)).first()


@router.post("/login")
def login(email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Step 1: Get the user from the auth table
    user = get_user_by_email(db, email.lower())

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Step 2: Verify the password
    stored_hash = user.hashed_password
    # Use the lowercase email as salt
    salt = email.lower()  # This uses the input email, converted to lowercase

    if not verify_password(password, stored_hash, salt):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Step 3: Generate JWT token
    access_token = generate_JWT({"user_email": user.email})

    # Step 4: Retrieve the employee information using the email
    employee = db.query(Employee).filter(func.lower(Employee.email) == user.email.lower()).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Step 5: Return login success with employee data
    return {
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "employee_info": {
                "staff_id": employee.staff_id,
                "first_name": employee.staff_fname,
                "last_name": employee.staff_lname,
                "department": employee.dept,
                "position": employee.position,
                "country": employee.country,
                "reporting_manager": employee.reporting_manager,
                "role": employee.role,
            },
        },
    }
