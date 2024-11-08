from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..arrangements.commons.models import LatestArrangement
from . import models
from .dataclasses import EmployeeFilters
from .models import DelegateLog, DelegationStatus, Employee

singapore_timezone = ZoneInfo("Asia/Singapore")


def get_employees(db: Session, filters: EmployeeFilters) -> List[models.Employee]:
    query = db.query(models.Employee)
    if filters.department:
        query = query.filter(models.Employee.dept == filters.department)
    return query.all()


def get_employee_by_staff_id(db: Session, staff_id: int) -> models.Employee:
    return db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    return db.query(models.Employee).filter(func.lower(models.Employee.email) == email).first()


def get_subordinates_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    return db.query(models.Employee).filter(models.Employee.reporting_manager == manager_id).all()


def get_existing_delegation(db: Session, staff_id: int, delegate_manager_id: int):
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
    existing_delegation = get_existing_delegation(db, staff_id, delegate_manager_id)
    if existing_delegation:
        return existing_delegation  # Prevent duplicate
    # Proceed to create a new delegation if none exists
    new_delegation = DelegateLog(
        manager_id=staff_id,
        delegate_manager_id=delegate_manager_id,
        date_of_delegation=datetime.now(singapore_timezone),
        status_of_delegation=DelegationStatus.pending,
    )
    db.add(new_delegation)
    db.commit()
    db.refresh(new_delegation)
    return new_delegation


def get_delegation_log_by_delegate(db: Session, staff_id: int):
    return (
        db.query(models.DelegateLog)
        .filter(models.DelegateLog.delegate_manager_id == staff_id)
        .filter(models.DelegateLog.status_of_delegation == DelegationStatus.pending)
        .first()
    )


def update_delegation_status(
    db: Session, delegation_log: DelegateLog, status: DelegationStatus, description: str = None
):
    delegation_log.status_of_delegation = status
    if description:
        delegation_log.description = description  # Add description to the log
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def update_pending_arrangements_for_delegate(
    db: Session, manager_id: int, delegate_manager_id: int
):
    db.query(LatestArrangement).filter(
        LatestArrangement.approving_officer == manager_id,
    ).update(
        {
            LatestArrangement.delegate_approving_officer: delegate_manager_id,
            LatestArrangement.update_datetime: datetime.now(singapore_timezone),
        },
    )

    db.commit()


# def get_delegation_log_by_manager(db: Session, staff_id: int):
#     """This function retrieves a delegation log entry by manager ID from the database.

#     :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
#     session that allows interaction with the database. It is used to query the database for delegation
#     logs
#     :type db: Session
#     :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
#     staff member or manager in the database. This parameter is used to filter and retrieve delegation
#     logs associated with a specific manager based on their ID
#     :type staff_id: int
#     :return: The function `get_delegation_log_by_manager` returns the first delegation log entry from
#     the database where the manager_id matches the provided staff_id.
#     """
#     return db.query(models.DelegateLog).filter(models.DelegateLog.manager_id == staff_id).first()


def get_delegation_log_by_manager(db: Session, staff_id: int):
    return db.query(models.DelegateLog).filter(models.DelegateLog.manager_id == staff_id).first()


def remove_delegate_from_arrangements(db: Session, delegate_manager_id: int):
    db.query(LatestArrangement).filter(
        LatestArrangement.delegate_approving_officer == delegate_manager_id,
    ).update(
        {
            LatestArrangement.delegate_approving_officer: None,
            LatestArrangement.update_datetime: datetime.now(singapore_timezone),
        }
    )

    db.commit()


def mark_delegation_as_undelegated(db: Session, delegation_log: models.DelegateLog):
    delegation_log.status_of_delegation = models.DelegationStatus.undelegated
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def get_sent_delegations(db: Session, staff_id: int):
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


def get_all_sent_delegations(db: Session, staff_id: int):
    return db.query(DelegateLog).filter(DelegateLog.manager_id == staff_id).all()


def get_all_received_delegations(db: Session, staff_id: int):
    return db.query(DelegateLog).filter(DelegateLog.delegate_manager_id == staff_id).all()


def get_employee_full_name(db: Session, staff_id: int):
    employee = db.query(Employee).filter(Employee.staff_id == staff_id).first()
    return f"{employee.staff_fname} {employee.staff_lname}" if employee else "Unknown"


def get_manager_of_employee(db: Session, emp: Employee) -> Employee:
    if emp.manager and emp.manager.staff_id != emp.staff_id:
        return emp.manager
    return None


def get_peer_employees(db: Session, manager_id: int) -> list[Employee]:
    return db.query(Employee).filter(Employee.reporting_manager == manager_id).all()


def is_employee_locked_in_delegation(db: Session, employee_id: int) -> bool:
    return (
        db.query(DelegateLog)
        .filter(
            or_(
                DelegateLog.manager_id == employee_id,
                DelegateLog.delegate_manager_id == employee_id,
            ),
            DelegateLog.status_of_delegation.in_(
                [DelegationStatus.pending, DelegationStatus.accepted]
            ),
        )
        .first()
        is not None
    )


def get_delegated_manager(db: Session, approving_officer_id: int) -> Optional[models.Employee]:
    # Query for active delegation where the original approving officer has delegated to someone
    delegation = (
        db.query(DelegateLog)
        .filter(
            DelegateLog.manager_id == approving_officer_id,
            DelegateLog.status_of_delegation == DelegationStatus.accepted,
        )
        .order_by(DelegateLog.date_of_delegation.desc())  # Get the most recent delegation
        .first()
    )

    if delegation:
        # Get the delegate approving officer's details
        delegate_manager = (
            db.query(models.Employee)
            .filter(models.Employee.staff_id == delegation.delegate_manager_id)
            .first()
        )
        return delegate_manager

    return None
