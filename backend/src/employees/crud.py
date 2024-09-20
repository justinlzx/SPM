from sqlalchemy.orm import Session

from . import models


def get_employee(db: Session, staff_id: int):
    return (
        db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()
    )
