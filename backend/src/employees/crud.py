from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models


def get_employee_by_staff_id(db: Session, staff_id: int) -> models.Employee:
    return db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    return db.query(models.Employee).filter(func.lower(models.Employee.email) == email).first()


def get_employees_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    return db.query(models.Employee).filter(models.Employee.reporting_manager == manager_id).all()
