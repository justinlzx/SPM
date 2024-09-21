from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ..auth.models import get_user_by_email
from ..employees.models import Employee
from ..auth.utils import generate_JWT, verify_password
from ..database import get_db

router = APIRouter()


# @router.post("/register")
# def register(
#     email: EmailStr = Form(...),
#     password: str = Form(...),
#     db: Session = Depends(get_db),
# ):
#     # Check if email already exists
#     if get_user_by_email(db, email):
#         raise HTTPException(status_code=400, detail="Email already exists")

#     # Hash the password (no need for staff_id as salt anymore, can use email as salt)
#     hashed_password = hash_password(password, email)

#     # Create the user in the database
#     create_user(db, email, hashed_password)
#     return {"message": "User registered successfully", "email": email}


@router.post("/login")
def login(
    email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    # Step 1: Get the user from the auth table
    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Step 2: Verify the password
    stored_hash = user.hashed_password
    if not verify_password(password, stored_hash, email):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Step 3: Generate JWT token
    access_token = generate_JWT({"user_email": email})

    # Step 4: Retrieve the employee information using the email
    employee = db.query(Employee).filter(Employee.email == email).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Step 5: Return login success with employee data
    return {
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "email": email,
            "employee_info": {
                "staff_id": employee.staff_id,
                "first_name": employee.staff_fname,
                "last_name": employee.staff_lname,
                "department": employee.dept,
                "position": employee.position,
                "country": employee.country,
                "reporting_manager": employee.reporting_manager,
                "role": employee.role
            }
        },
    }
