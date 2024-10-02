from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from ..auth.models import get_user_by_email, Auth
from ..employees.models import Employee
from ..auth.utils import generate_JWT, verify_password, hash_password
from ..database import get_db

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Update the get_user_by_email function
def get_user_by_email(db: Session, email: str):
    return db.query(Auth).filter(func.lower(Auth.email) == func.lower(email)).first()


@router.post("/login")
def login(email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Log the input email
    logger.debug(f"Input email: {email}")

    # Step 1: Get the user from the auth table
    user = get_user_by_email(db, email.lower())

    if not user:
        logger.warning(f"User not found for email: {email.lower()}")
        raise HTTPException(status_code=400, detail="Invalid email or password")

    logger.debug(f"User found: {user.email}")

    # Step 2: Verify the password
    stored_hash = user.hashed_password
    # Use the original email as salt
    salt = user.email  # This should be the original email stored in the database

    # Log the hashed input password and stored hash for comparison
    input_hash = hash_password(password, salt)
    logger.debug(f"Salt used (original email): {salt}")
    logger.debug(f"Hashed input password: {input_hash}")
    logger.debug(f"Stored hashed password: {stored_hash}")

    if not verify_password(password, stored_hash, salt):
        logger.warning(f"Invalid password for email: {email}")
        raise HTTPException(status_code=400, detail="Invalid email or password")

    logger.debug("Password verified successfully")

    # Step 3: Generate JWT token
    access_token = generate_JWT({"user_email": user.email})
    logger.debug("JWT token generated")

    # Step 4: Retrieve the employee information using the email
    employee = db.query(Employee).filter(func.lower(Employee.email) == user.email.lower()).first()

    if not employee:
        logger.warning(f"Employee not found for email: {user.email}")
        raise HTTPException(status_code=404, detail="Employee not found")

    logger.debug(f"Employee found: {employee.email}")

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
