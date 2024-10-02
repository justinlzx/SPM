from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from ..database import get_db
from ..employees.models import Employee, get_employee_by_staff_id, get_employees_by_manager_id
from ..employees.schemas import EmployeeBase, EmployeePeerResponse
from .crud import get_employee, get_employee_by_email
import pandas as pd
import os

router = APIRouter()


@router.get("/manager/peermanager/{staff_id}", response_model=EmployeePeerResponse)
def get_reporting_manager(staff_id: int, db: Session = Depends(get_db)):
    try:
        emp: Employee = get_employee_by_staff_id(db, staff_id)

        print(f"staff id: {emp.staff_id}")
        manager: Employee = emp.manager

        # If employee reports to themselves, set manager to None
        if manager and manager.staff_id == emp.staff_id:
            manager = None

        # Get peer employees and convert them to Pydantic models
        peer_list: List[Employee] = (
            get_employees_by_manager_id(db, emp.reporting_manager) if emp.reporting_manager else []
        )

        peer_employees = [EmployeeBase.model_validate(peer) for peer in peer_list]

        print(f"num results: {len(peer_employees)}")

        return {
            "manager_id": manager.staff_id if manager else None,
            "peer_employees": peer_employees,
        }

    except NoResultFound:
        raise HTTPException(status_code=404, detail="Employee not found")


@router.get("/{staff_id}", response_model=EmployeeBase)
def read_employee(staff_id: int, db: Session = Depends(get_db)):
    """
    Get an employee by staff_id.
    """
    employee = get_employee(db, staff_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee  # Pydantic model (EmployeeBase) will handle serialization


@router.get("/email/{email}", response_model=EmployeeBase)
def read_employee_by_email(email: str, db: Session = Depends(get_db)):
    """
    Get an employee by email.
    """
    employee = get_employee_by_email(db, email)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee  # Pydantic model (EmployeeBase) will handle serialization


@router.get("/manager/employees/{staff_id}", response_model=List[EmployeeBase])
def get_employees_under_manager(staff_id: int, db: Session = Depends(get_db)):
    """
    Get a list of employees under a specific manager by their staff_id.
    """
    # Check if the employee is a manager
    employees_under_manager: List[Employee] = get_employees_by_manager_id(db, staff_id)

    if not employees_under_manager:
        raise HTTPException(status_code=404, detail="No employees found under this manager")

    # Convert to Pydantic models
    return [EmployeeBase.model_validate(employee) for employee in employees_under_manager]


# Load the employee data from CSV
CSV_FILE_PATH = os.path.join("src", "init_db", "employee.csv")  # Adjust the path as necessary
employee_df = pd.read_csv(CSV_FILE_PATH)


@router.get("/get_staff_id/email")
async def get_staff_id(email: str) -> JSONResponse:
    try:
        # Find the staff ID for the given email
        employee_record = employee_df[employee_df["Email"] == email]  # Use the correct column name

        if not employee_record.empty:
            # Convert the staff_id to a native Python int
            staff_id = int(employee_record["Staff_ID"].values[0])  # Convert to int
            return JSONResponse(content={"staff_id": staff_id})
        else:
            raise HTTPException(status_code=404, detail="Employee not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
