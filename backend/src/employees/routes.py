from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from ..database import get_db
from ..employees.models import Employee
from ..employees.models import get_employee_by_staff_id, get_employees_by_manager_id
from .crud import get_employee_by_email, get_employee
from ..employees.schemas import EmployeeBase, EmployeePeerResponse

router = APIRouter()


@router.get("/peer_manager/{staff_id}", response_model=EmployeePeerResponse)
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
            get_employees_by_manager_id(db, emp.reporting_manager)
            if emp.reporting_manager
            else []
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
