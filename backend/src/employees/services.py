from typing import List

from sqlalchemy.orm import Session

from . import crud, exceptions, models


def get_manager_by_employee_staff_id(db: Session, staff_id: int) -> models.Employee:
    emp: models.Employee = get_employee_by_staff_id(db, staff_id)
    print(f"staff id: {emp.staff_id}")
    manager: models.Employee = emp.manager

    # If employee reports to themselves, set manager to None
    if manager and manager.staff_id == emp.staff_id:
        manager = None

    return manager


def get_employee_by_staff_id(db: Session, staff_id: int) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_staff_id(db, staff_id)

    if not employee:
        raise exceptions.EmployeeNotFound()

    return employee


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_email(db, email)

    if not employee:
        raise exceptions.EmployeeNotFound()

    return employee


def get_employees_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    employees: List[models.Employee] = crud.get_employees_by_manager_id(db, manager_id)

    if not employees:
        raise exceptions.ManagerNotFound()

    return employees
