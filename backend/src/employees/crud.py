from sqlalchemy.orm import Session

from . import models


def get_employee(db: Session, staff_id: int):
    return (
        db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()
    )


def get_employee_by_email(db: Session, email: str):
    return (
        db.query(models.Employee).filter(models.Employee.email == email).first()
    )
