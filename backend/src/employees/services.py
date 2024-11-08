import os
from enum import Enum
from typing import List, Tuple, Union

from sqlalchemy.orm import Session

from ..logger import logger
from ..notifications.commons.dataclasses import DelegateNotificationConfig
from ..notifications.email_notifications import craft_and_send_email
from ..utils import convert_model_to_pydantic_schema
from . import crud, exceptions, models, schemas
from .dataclasses import EmployeeFilters

JACK_SIM_STAFF_ID = 130002


def get_employees(db: Session, filters: EmployeeFilters):
    employees = crud.get_employees(db, filters)
    employees_pydantic = convert_model_to_pydantic_schema(employees, schemas.EmployeeBase)
    return employees_pydantic


def get_reporting_manager_and_peer_employees(db: Session, staff_id: int):
    # Auto Approve for Jack Sim and Skip manager check
    if staff_id == JACK_SIM_STAFF_ID:
        return schemas.EmployeePeerResponse(manager_id=None, peer_employees=[])

    manager: models.Employee = get_manager_by_subordinate_id(db, staff_id)

    if not manager:
        return schemas.EmployeePeerResponse(manager_id=None, peer_employees=[])

    # Get list of peer employees
    peer_employees: List[models.Employee] = get_subordinates_by_manager_id(db, manager.staff_id)

    # Filter out the manager from the peer employees
    peer_employees = [peer for peer in peer_employees if peer.staff_id != manager.staff_id]

    # Convert peer employees to Pydantic model
    peer_employees_pydantic: List[schemas.EmployeeBase] = convert_model_to_pydantic_schema(
        peer_employees, schemas.EmployeeBase
    )

    logger.info(f"Num results: {len(peer_employees)}")

    # Format to response model
    response = schemas.EmployeePeerResponse(
        manager_id=manager.staff_id, peer_employees=peer_employees_pydantic
    )

    return response


# The class `DelegationApprovalStatus` defines an enumeration for delegation approval statuses with
# values "accepted" and "rejected".
class DelegationApprovalStatus(Enum):
    accept = "accepted"
    reject = "rejected"


def get_manager_by_subordinate_id(
    db: Session, staff_id: int
) -> Union[Tuple[models.Employee, List[models.Employee]], Tuple[None, None]]:
    # Auto Approve for Jack Sim and bypass manager check
    if staff_id == JACK_SIM_STAFF_ID:
        return None, None  # Auto-approve for Jack Sim

    # Retrieve the employee
    emp = get_employee_by_id(db, staff_id)
    if not emp:
        raise exceptions.EmployeeNotFoundException(staff_id)

    # Get the manager of the employee
    manager = crud.get_manager_of_employee(db, emp)
    if not manager:
        return None, None  # Return None if there's no valid manager

    # Check if the manager has delegated their authority
    delegated_manager = crud.get_delegated_manager(db, manager.staff_id)
    if delegated_manager:
        manager = delegated_manager

    # Retrieve all peers reporting to the manager
    all_peers = crud.get_peer_employees(db, manager.staff_id)

    # Filter out peers who are either locked in a delegation relationship or have the ID 130002
    unlocked_peers = [
        peer
        for peer in all_peers
        if not crud.is_employee_locked_in_delegation(db, peer.staff_id)
        and peer.staff_id != JACK_SIM_STAFF_ID
    ]

    logger.info(
        f"Unlocked peers for manager {manager.staff_id}: {[peer.staff_id for peer in unlocked_peers]}"
    )
    return manager, unlocked_peers


def get_employee_by_id(db: Session, staff_id: int) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_staff_id(db, staff_id)

    if not employee:
        raise exceptions.EmployeeNotFoundException(staff_id)

    return employee


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_email(db, email)

    if not employee:
        raise exceptions.EmployeeGenericNotFoundException()

    return employee


def get_subordinates_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    employees: List[models.Employee] = crud.get_subordinates_by_manager_id(db, manager_id)

    if not employees:
        raise exceptions.ManagerWithIDNotFoundException(manager_id=manager_id)

    return employees


def get_peers_by_staff_id(db: Session, staff_id: int) -> List[models.Employee]:
    employee: models.Employee = get_employee_by_id(db, staff_id)
    peer_employees: List[models.Employee] = crud.get_subordinates_by_manager_id(
        db, employee.reporting_manager
    )

    return peer_employees


async def delegate_manager(staff_id: int, delegate_manager_id: int, db: Session):
    # Step 1: Check for existing delegation
    existing_delegation = crud.get_existing_delegation(db, staff_id, delegate_manager_id)
    if existing_delegation:
        return "Delegation already exists for either the manager or delegatee."

    # Step 2: Log the new delegation
    try:
        new_delegation = crud.create_delegation(db, staff_id, delegate_manager_id)

        # Step 3: Fetch employee info for notifications
        manager_employee = get_employee_by_id(db, staff_id)
        delegatee_employee = get_employee_by_id(db, delegate_manager_id)

        # Step 4: Craft and send email notifications
        notification_config = DelegateNotificationConfig(
            delegator=manager_employee, delegatee=delegatee_employee, action="delegate"
        )
        if os.getenv("TESTING") == "false":
            await craft_and_send_email(notification_config)

        return new_delegation  # Return the created delegation log

    except Exception as e:
        db.rollback()
        raise e


async def process_delegation_status(
    staff_id: int, status: DelegationApprovalStatus, db: Session, description: str = None
):
    # Step 1: Fetch the delegation log
    delegation_log = crud.get_delegation_log_by_delegate(db, staff_id)
    if not delegation_log:
        return "Delegation log not found."

    # Step 2: Fetch manager and delegatee details for email notification
    manager_employee = get_employee_by_id(db, delegation_log.manager_id)
    delegatee_employee = get_employee_by_id(db, staff_id)

    if status == DelegationApprovalStatus.accept:
        # Approve delegation, update pending arrangements, and save the optional description
        delegation_log = crud.update_delegation_status(
            db, delegation_log, models.DelegationStatus.accepted, description=description
        )
        crud.update_pending_arrangements_for_delegate(
            db, delegation_log.manager_id, delegation_log.delegate_manager_id
        )

        # Send approval emails
        notification_config = DelegateNotificationConfig(
            delegator=manager_employee, delegatee=delegatee_employee, action="approved"
        )
        if os.getenv("TESTING") == "false":
            await craft_and_send_email(notification_config)

    elif status == DelegationApprovalStatus.reject:
        # Reject delegation and save the required description
        delegation_log = crud.update_delegation_status(
            db, delegation_log, models.DelegationStatus.rejected, description=description
        )

        # Send rejection emails
        notification_config = DelegateNotificationConfig(
            delegator=manager_employee, delegatee=delegatee_employee, action="rejected"
        )
        if os.getenv("TESTING") == "false":
            await craft_and_send_email(notification_config)

    return delegation_log


async def undelegate_manager(staff_id: int, db: Session):
    # Step 1: Fetch the delegation log for the manager
    delegation_log = crud.get_delegation_log_by_manager(db, staff_id)
    if not delegation_log:
        return "Delegation log not found."

    # Step 2: Remove delegate from arrangements
    crud.remove_delegate_from_arrangements(db, delegation_log.delegate_manager_id)

    # Step 3: Mark the delegation as 'undelegated'
    delegation_log = crud.mark_delegation_as_undelegated(db, delegation_log)

    # Step 4: Fetch manager and delegatee info for notifications
    manager_employee = get_employee_by_id(db, delegation_log.manager_id)
    delegatee_employee = get_employee_by_id(db, delegation_log.delegate_manager_id)

    # Send notification emails
    notification_config = DelegateNotificationConfig(
        delegator=manager_employee, delegatee=delegatee_employee, action="undelegate"
    )
    if os.getenv("TESTING") == "false":
        await craft_and_send_email(notification_config)

    return delegation_log


def view_delegations(staff_id: int, db: Session):
    # Retrieve sent delegations by the manager
    sent_delegations = crud.get_sent_delegations(db, staff_id)
    # Retrieve delegations pending approval by the manager
    pending_approval_delegations = crud.get_pending_approval_delegations(db, staff_id)

    # Format the sent delegations data
    sent_delegations_data = [
        {
            "staff_id": delegation.delegate_manager_id,
            "full_name": crud.get_employee_full_name(db, delegation.delegate_manager_id),
            "date_of_delegation": delegation.date_of_delegation,
            "status_of_delegation": delegation.status_of_delegation,
        }
        for delegation in sent_delegations
    ]

    # Format the pending approval delegations data
    pending_approval_delegations_data = [
        {
            "staff_id": delegation.manager_id,
            "full_name": crud.get_employee_full_name(db, delegation.manager_id),
            "date_of_delegation": delegation.date_of_delegation,
            "status_of_delegation": delegation.status_of_delegation,
        }
        for delegation in pending_approval_delegations
    ]

    return {
        "sent_delegations": sent_delegations_data,
        "pending_approval_delegations": pending_approval_delegations_data,
    }


def view_all_delegations(staff_id: int, db: Session):
    # Retrieve all delegations sent by the manager
    sent_delegations = crud.get_all_sent_delegations(db, staff_id)
    # Retrieve all delegations received by the manager
    received_delegations = crud.get_all_received_delegations(db, staff_id)

    # Format sent delegations data
    sent_delegations_data = [
        {
            "manager_id": delegation.manager_id,
            "manager_name": crud.get_employee_full_name(db, delegation.manager_id),
            "delegate_manager_id": delegation.delegate_manager_id,
            "delegate_manager_name": crud.get_employee_full_name(
                db, delegation.delegate_manager_id
            ),
            "date_of_delegation": delegation.date_of_delegation,
            "updated_datetime": delegation.update_datetime,
            "status_of_delegation": delegation.status_of_delegation,
        }
        for delegation in sent_delegations
    ]

    # Format received delegations data
    received_delegations_data = [
        {
            "manager_id": delegation.manager_id,
            "manager_name": crud.get_employee_full_name(db, delegation.manager_id),
            "delegate_manager_id": delegation.delegate_manager_id,
            "delegate_manager_name": crud.get_employee_full_name(
                db, delegation.delegate_manager_id
            ),
            "date_of_delegation": delegation.date_of_delegation,
            "updated_datetime": delegation.update_datetime,
            "status_of_delegation": delegation.status_of_delegation,
        }
        for delegation in received_delegations
    ]

    return {
        "sent_delegations": sent_delegations_data,
        "received_delegations": received_delegations_data,
    }
