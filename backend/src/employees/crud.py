from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.arrangements.models import LatestArrangement
from src.employees.models import Employee

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


def get_delegation_log_by_delegate(db: Session, staff_id: int):
    """
    Fetch the delegation log entry for a given delegate manager.
    """
    return (
        db.query(models.DelegateLog)
        .filter(models.DelegateLog.delegate_manager_id == staff_id)
        .first()
    )


def update_delegation_status(
    db: Session, delegation_log: models.DelegateLog, status: models.DelegationStatus
):
    """
    Update the delegation log status and commit the change to the database.
    """
    delegation_log.status_of_delegation = status
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def update_pending_arrangements_for_delegate(
    db: Session, manager_id: int, delegate_manager_id: int
):
    """
    Update pending approval requests for the original manager to assign the delegate.
    """
    pending_arrangements = (
        db.query(LatestArrangement)
        .filter(
            LatestArrangement.approving_officer == manager_id,
            LatestArrangement.current_approval_status.in_(
                ["pending approval", "pending withdrawal"]
            ),
        )
        .all()
    )

    for arrangement in pending_arrangements:
        arrangement.delegate_approving_officer = delegate_manager_id
        db.add(arrangement)

    db.commit()


def get_delegation_log_by_manager(db: Session, staff_id: int):
    """
    Fetch the delegation log entry for a given manager.
    """
    return db.query(models.DelegateLog).filter(models.DelegateLog.manager_id == staff_id).first()


def remove_delegate_from_arrangements(db: Session, delegate_manager_id: int):
    """
    Update pending approval requests by removing the delegate and restoring the original manager.
    """
    pending_arrangements = (
        db.query(LatestArrangement)
        .filter(
            LatestArrangement.delegate_approving_officer == delegate_manager_id,
            LatestArrangement.current_approval_status.in_(
                ["pending approval", "pending withdrawal"]
            ),
        )
        .all()
    )

    for arrangement in pending_arrangements:
        arrangement.delegate_approving_officer = None  # Remove the delegate manager
        db.add(arrangement)

    db.commit()


def mark_delegation_as_undelegated(db: Session, delegation_log: models.DelegateLog):
    """
    Mark the delegation as 'undelegated' and commit the changes.
    """
    delegation_log.status_of_delegation = models.DelegationStatus.undelegated
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def get_sent_delegations(db: Session, staff_id: int):
    """
    Retrieve delegations sent by the manager with statuses pending and accepted.
    """
    return (
        db.query(models.DelegateLog)
        .filter(
            models.DelegateLog.manager_id == staff_id,
            models.DelegateLog.status_of_delegation.in_(
                [models.DelegationStatus.pending, models.DelegationStatus.accepted]
            ),
        )
        .all()
    )


def get_pending_approval_delegations(db: Session, staff_id: int):
    """
    Retrieve delegations awaiting manager's approval with statuses pending and accepted.
    """
    return (
        db.query(models.DelegateLog)
        .filter(
            models.DelegateLog.delegate_manager_id == staff_id,
            models.DelegateLog.status_of_delegation.in_(
                [models.DelegationStatus.pending, models.DelegationStatus.accepted]
            ),
        )
        .all()
    )


def get_employee_full_name(db: Session, staff_id: int):
    """
    Fetch the full name of an employee given their staff_id.
    """
    employee = db.query(Employee).filter(Employee.staff_id == staff_id).first()
    return f"{employee.staff_fname} {employee.staff_lname}" if employee else "Unknown"
