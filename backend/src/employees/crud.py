from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models


def get_employee_by_staff_id(db: Session, staff_id: int) -> models.Employee:
    return db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    return db.query(models.Employee).filter(func.lower(models.Employee.email) == email).first()


def get_subordinates_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    return db.query(models.Employee).filter(models.Employee.reporting_manager == manager_id).all()


def get_existing_delegation(db: Session, staff_id: int, delegate_manager_id: int):
    """
    Check if there's an existing delegation for the manager or delegatee.
    """
    return (
        db.query(models.DelegateLog)
        .filter(
            (models.DelegateLog.manager_id == staff_id)
            | (models.DelegateLog.delegate_manager_id == delegate_manager_id)
        )
        .filter(
            models.DelegateLog.status_of_delegation.in_(
                [models.DelegationStatus.pending, models.DelegationStatus.accepted]
            )
        )
        .first()
    )


def create_delegation(db: Session, staff_id: int, delegate_manager_id: int):
    """
    Log a new delegation in the delegate_logs table.
    """
    new_delegation = models.DelegateLog(
        manager_id=staff_id,
        delegate_manager_id=delegate_manager_id,
        date_of_delegation=datetime.utcnow(),
        status_of_delegation=models.DelegationStatus.pending,  # Default to pending
    )
    db.add(new_delegation)
    db.commit()
    db.refresh(new_delegation)
    return new_delegation
