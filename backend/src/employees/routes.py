from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .crud import get_employee
from .models import Employee
from ..database import get_db

router = APIRouter()


@router.get("/employees/{staff_id}", response_model=dict)
def read_employee(staff_id: int, db: Session = Depends(get_db)):
    """
    Get an employee by staff_id.
    """
    employee = get_employee(db, staff_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "staff_id": employee.staff_id,
        "first_name": employee.staff_fname,
        "last_name": employee.staff_lname,
        "department": employee.dept,
        "position": employee.position,
        "country": employee.country,
        "email": employee.email,
        "reporting_manager": employee.reporting_manager,
        "role": employee.role,
    }
