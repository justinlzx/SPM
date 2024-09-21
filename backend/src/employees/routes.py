from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from ..database import get_db
from ..employees.models import Employee
from ..employees.models import get_employee_by_staff_id, get_employees_by_manager_id

router = APIRouter()


@router.get("/manager/peer/{staff_id}")
def get_reporting_manager(staff_id: int, db: Session = Depends(get_db)):
    try:
        emp: Employee = get_employee_by_staff_id(db, staff_id)

        print(f"staff id: {emp.staff_id}")
        manager: Employee = emp.manager
        print(f"manager id: {manager.staff_id}")
        peer_list: List[Employee] = get_employees_by_manager_id(db, manager.staff_id)

        print(f"num results: {len(peer_list)}")

        return {"manager_id": manager.staff_id, "peer_employees": peer_list}

    except NoResultFound:
        raise HTTPException(status_code=404, detail="Employee not found")
