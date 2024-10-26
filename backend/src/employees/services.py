from enum import Enum
from typing import List

from sqlalchemy.orm import Session

from src.email.routes import send_email
from src.notifications.email_notifications import craft_email_content_for_delegation

from . import crud, exceptions, models


# The class `DelegationApprovalStatus` defines an enumeration for delegation approval statuses with
# values "accepted" and "rejected".
class DelegationApprovalStatus(Enum):
    accept = "accepted"
    reject = "rejected"


def get_manager_by_subordinate_id(db: Session, staff_id: int) -> models.Employee:
    """
    Retrieve the manager for a given subordinate ID, ensuring the manager's peer employees are
    not locked in an active delegation relationship, and excluding the specific ID 130002.
    """
    # Auto Approve for Jack Sim and bypass manager check
    if staff_id == 130002:
        return None  # Auto-approve for Jack Sim

    # Retrieve the employee
    emp = get_employee_by_id(db, staff_id)
    if not emp:
        raise exceptions.EmployeeNotFoundException("Employee not found.")

    # Get the manager of the employee
    manager = crud.get_manager_of_employee(db, emp)
    if not manager:
        return None  # Return None if there's no valid manager

    # Retrieve all peers reporting to the manager
    all_peers = crud.get_peer_employees(db, manager.staff_id)

    # Filter out peers who are either locked in a delegation relationship or have the ID 130002
    unlocked_peers = [
        peer
        for peer in all_peers
        if not crud.is_employee_locked_in_delegation(db, peer.staff_id) and peer.staff_id != 130002
    ]

    print(
        f"Unlocked peers for manager {manager.staff_id}: {[peer.staff_id for peer in unlocked_peers]}"
    )
    return manager, unlocked_peers


def get_employee_by_id(db: Session, staff_id: int) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_staff_id(db, staff_id)

    if not employee:
        raise exceptions.EmployeeNotFoundException()

    return employee


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    employee: models.Employee = crud.get_employee_by_email(db, email)

    if not employee:
        raise exceptions.EmployeeNotFoundException()

    return employee


def get_subordinates_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    employees: List[models.Employee] = crud.get_subordinates_by_manager_id(db, manager_id)

    if not employees:
        raise exceptions.ManagerNotFoundException()

    return employees


def get_peers_by_staff_id(db: Session, staff_id: int) -> List[models.Employee]:
    employee: models.Employee = get_employee_by_id(db, staff_id)
    peer_employees: List[models.Employee] = get_subordinates_by_manager_id(
        db, employee.reporting_manager
    )

    return peer_employees


async def delegate_manager(staff_id: int, delegate_manager_id: int, db: Session):
    """
    Delegate the approval responsibility of a manager to another staff member.
    Returns a message if an existing delegation is found, otherwise logs the new delegation and sends email notifications.
    """
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
        manager_subject, manager_content = craft_email_content_for_delegation(
            manager_employee, delegatee_employee, "delegate"
        )
        await send_email(manager_employee.email, manager_subject, manager_content)

        delegatee_subject, delegatee_content = craft_email_content_for_delegation(
            delegatee_employee, manager_employee, "delegated_to"
        )
        await send_email(delegatee_employee.email, delegatee_subject, delegatee_content)

        return new_delegation  # Return the created delegation log

    except Exception as e:
        db.rollback()
        raise e


async def process_delegation_status(
    staff_id: int, status: DelegationApprovalStatus, db: Session, description: str = None
):
    """
    Process the update of delegation status, save the description, and handle notifications.
    """
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
        manager_subject, manager_content = craft_email_content_for_delegation(
            manager_employee, delegatee_employee, "approved"
        )
        await send_email(manager_employee.email, manager_subject, manager_content)

        delegate_subject, delegate_content = craft_email_content_for_delegation(
            delegatee_employee, manager_employee, "approved_for_delegate"
        )
        await send_email(delegatee_employee.email, delegate_subject, delegate_content)

    elif status == DelegationApprovalStatus.reject:
        # Reject delegation and save the required description
        delegation_log = crud.update_delegation_status(
            db, delegation_log, models.DelegationStatus.rejected, description=description
        )

        # Send rejection emails
        manager_subject, manager_content = craft_email_content_for_delegation(
            manager_employee, delegatee_employee, "rejected"
        )
        await send_email(manager_employee.email, manager_subject, manager_content)

        delegate_subject, delegate_content = craft_email_content_for_delegation(
            delegatee_employee, manager_employee, "rejected_for_delegate"
        )
        await send_email(delegatee_employee.email, delegate_subject, delegate_content)

    return delegation_log


async def undelegate_manager(staff_id: int, db: Session):
    """
    Process the undelegation of a manager, update arrangements, and send notifications.
    """
    # Step 1: Fetch the delegation log for the manager
    delegation_log = crud.get_delegation_log_by_manager(db, staff_id)
    if not delegation_log:
        return "Delegation log not found."

    # Step 2: Check if the delegation status is 'accepted'
    if delegation_log.status_of_delegation != models.DelegationStatus.accepted:
        return "Delegation must be approved to undelegate."

    # Step 3: Remove delegate from arrangements
    crud.remove_delegate_from_arrangements(db, delegation_log.delegate_manager_id)

    # Step 4: Mark the delegation as 'undelegated'
    delegation_log = crud.mark_delegation_as_undelegated(db, delegation_log)

    # Step 5: Fetch manager and delegatee info for notifications
    manager_employee = get_employee_by_id(db, delegation_log.manager_id)
    delegatee_employee = get_employee_by_id(db, delegation_log.delegate_manager_id)

    # Send notification emails
    manager_subject, manager_content = craft_email_content_for_delegation(
        manager_employee, delegatee_employee, "withdrawn"
    )
    await send_email(manager_employee.email, manager_subject, manager_content)

    delegate_subject, delegate_content = craft_email_content_for_delegation(
        delegatee_employee, manager_employee, "withdrawn_for_delegate"
    )
    await send_email(delegatee_employee.email, delegate_subject, delegate_content)

    return delegation_log


def view_delegations(staff_id: int, db: Session):
    """
    Retrieve delegations sent by a manager and those pending approval, formatting each with relevant fields.
    """
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
    """
    Retrieve all delegations sent and received by a specified manager, formatting each with relevant fields.
    """
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
