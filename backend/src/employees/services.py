from enum import Enum
from typing import List, Tuple, Union

from sqlalchemy.orm import Session

from ..notifications.commons.dataclasses import DelegateNotificationConfig
from ..notifications.email_notifications import craft_and_send_email
from ..utils import convert_model_to_pydantic_schema
from . import crud, exceptions, models, schemas
from .dataclasses import EmployeeFilters


def get_employees(db: Session, filters: EmployeeFilters):
    employees = crud.get_employees(db, filters)
    employees_pydantic = convert_model_to_pydantic_schema(employees, schemas.EmployeeBase)
    return employees_pydantic


def get_reporting_manager_and_peer_employees(db: Session, staff_id: int):
    # Auto Approve for Jack Sim and Skip manager check
    if staff_id == 130002:
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

    print(f"Num results: {len(peer_employees)}")

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
    """
    The function `get_manager_by_subordinate_id` retrieves the manager for a given subordinate ID,
    ensuring that the manager's peer employees are not locked in an active delegation relationship and
    excluding a specific ID.

    :param db: The `db` parameter in the `get_manager_by_subordinate_id` function is of type `Session`,
    which is likely an instance of a database session that allows interaction with the database. This
    parameter is used to query the database for employee and manager information
    :type db: Session
    :param staff_id: The function `get_manager_by_subordinate_id` is designed to retrieve the manager
    for a given subordinate ID while ensuring that the manager's peer employees are not locked in an
    active delegation relationship and excluding the specific ID 130002
    :type staff_id: int
    :return: The function `get_manager_by_subordinate_id` is returning a tuple containing the manager of
    the employee and a list of unlocked peers reporting to the manager.
    """
    # Auto Approve for Jack Sim and bypass manager check
    if staff_id == 130002:
        return None, None  # Auto-approve for Jack Sim

    # Retrieve the employee
    emp = get_employee_by_id(db, staff_id)
    if not emp:
        raise exceptions.EmployeeNotFoundException(staff_id)

    # Get the manager of the employee
    manager = crud.get_manager_of_employee(db, emp)
    if not manager:
        return None, None  # Return None if there's no valid manager

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
    """This function retrieves an employee from the database by their staff ID and raises an
    exception if the employee is not found.

    :param db: The `db` parameter is of type `Session`, which is likely referring to a database session
    object used for database operations. This parameter is used to interact with the database to
    retrieve information about employees
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of an
    employee in the database. It is used to retrieve the employee information from the database based on
    this specific identifier
    :type staff_id: int
    :return: an instance of the `Employee` model.
    """
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
    """
    The function `get_peers_by_staff_id` retrieves a list of employees who report to the same manager as
    the employee with the given staff ID.

    :param db: The `db` parameter is of type `Session`, which likely represents a database session
    object used to interact with the database. It is used to query the database for employee information
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
    staff member in the database. It is used to retrieve information about a specific employee, such as
    their reporting manager and peers
    :type staff_id: int
    :return: The function `get_peers_by_staff_id` returns a list of `models.Employee` objects
    representing the peers (employees who have the same reporting manager) of the employee with the
    specified `staff_id`.
    """
    employee: models.Employee = get_employee_by_id(db, staff_id)
    peer_employees: List[models.Employee] = crud.get_subordinates_by_manager_id(
        db, employee.reporting_manager
    )

    return peer_employees


async def delegate_manager(staff_id: int, delegate_manager_id: int, db: Session):
    """
    The `delegate_manager` function handles the delegation of a staff member to a manager, including
    checking for existing delegations, logging the new delegation, fetching employee info, and sending
    email notifications.

    :param staff_id: The `staff_id` parameter in the `delegate_manager` function represents the ID of
    the staff member whose delegation is being managed or updated. This ID is used to identify the staff
    member who is delegating tasks to another manager
    :type staff_id: int
    :param delegate_manager_id: The `delegate_manager_id` parameter in the `delegate_manager` function
    represents the unique identifier of the manager to whom the delegation is being assigned. This
    parameter is used to specify the manager who will be responsible for handling the delegated tasks on
    behalf of the staff member identified by `staff_id`
    :type delegate_manager_id: int
    :param db: The `db` parameter in the `delegate_manager` function is an instance of a database
    session. It is used to interact with the database to perform operations like checking for existing
    delegations, creating new delegations, and fetching employee information for notifications. The
    database session allows the function to query and manipulate
    :type db: Session
    :return: The function `delegate_manager` returns either a message indicating that the delegation
    already exists for either the manager or delegatee, or it returns the created delegation log if the
    delegation was successfully created and email notifications were sent to the manager and delegatee.
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
        notification_config = DelegateNotificationConfig(
            delegator=manager_employee, delegatee=delegatee_employee, action="delegate"
        )
        await craft_and_send_email(notification_config)

        return new_delegation  # Return the created delegation log

    except Exception as e:
        db.rollback()
        raise e


async def process_delegation_status(
    staff_id: int, status: DelegationApprovalStatus, db: Session, description: str = None
):
    """
    The function `process_delegation_status` handles the approval or rejection of a delegation request,
    updates the status accordingly, and sends email notifications to the manager and delegatee.

    :param staff_id: The `staff_id` parameter represents the ID of the staff member for whom the
    delegation status is being processed. This ID is used to fetch information about the staff member
    from the database and perform actions related to their delegation status
    :type staff_id: int
    :param status: The `status` parameter in the `process_delegation_status` function is of type
    `DelegationApprovalStatus`, which is used to determine whether the delegation should be accepted or
    rejected. It is an enum that likely has two possible values: `accept` and `reject`
    :type status: DelegationApprovalStatus
    :param db: The `db` parameter in the `process_delegation_status` function is typically an instance
    of a database session that allows you to interact with the database. It is used to perform database
    operations like fetching data, updating records, and committing transactions within the function
    :type db: Session
    :param description: The `description` parameter in the `process_delegation_status` function is an
    optional parameter that allows you to provide additional information or comments related to the
    delegation status update. It is a string type parameter that can be used to describe the reason for
    approval or rejection of the delegation. If provided, this
    :type description: str
    :return: The `process_delegation_status` function returns the updated delegation log after
    processing the delegation status based on the provided approval status (accept or reject). If the
    delegation log is not found, it returns the message "Delegation log not found".
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
        notification_config = DelegateNotificationConfig(
            delegator=manager_employee, delegatee=delegatee_employee, action="approved"
        )
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
        await craft_and_send_email(notification_config)

    return delegation_log


async def undelegate_manager(staff_id: int, db: Session):
    """
    The function `undelegate_manager` handles the process of withdrawing a delegation for a manager in a
    system, including updating the delegation status, removing the delegate from arrangements, and
    sending notification emails.

    :param staff_id: The `staff_id` parameter is the unique identifier of the manager whose delegation
    is being undelegated
    :type staff_id: int
    :param db: The `db` parameter in the `undelegate_manager` function is an instance of a database
    session. It is used to interact with the database to perform operations like fetching data, updating
    records, and committing transactions. In this context, it is likely an instance of a database
    session object that allows the
    :type db: Session
    :return: The function `undelegate_manager` returns the `delegation_log` object after performing the
    necessary steps to undelegate a manager.
    """
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
    await craft_and_send_email(notification_config)

    return delegation_log


def view_delegations(staff_id: int, db: Session):
    """This Python function retrieves and formats sent delegations by a manager and those pending
    approval from a database.

    :param staff_id: The `staff_id` parameter in the `view_delegations` function represents the unique
    identifier of the manager whose delegations are being viewed. This ID is used to retrieve the
    delegations sent by the manager and those pending approval in the database
    :type staff_id: int
    :param db: The `db` parameter in the `view_delegations` function is of type `Session`. This
    parameter is likely referring to a database session object that is used to interact with the
    database. It is commonly used in SQLAlchemy to perform database operations within a session context
    :type db: Session
    :return: The `view_delegations` function returns a dictionary containing two keys:
    "sent_delegations" and "pending_approval_delegations". The values associated with these keys are
    lists of dictionaries, where each dictionary represents a delegation with relevant fields such as
    staff ID, full name, date of delegation, and status of delegation. The "sent_delegations" key holds
    data for delegations sent
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
    The function `view_all_delegations` retrieves and formats both sent and received delegations data
    for a specific staff member.

    :param staff_id: The `staff_id` parameter in the `view_all_delegations` function represents the
    unique identifier of the manager for whom you want to view all delegations. This ID is used to
    retrieve both the delegations sent by the manager and the delegations received by the manager from
    the database
    :type staff_id: int
    :param db: The `db` parameter in the `view_all_delegations` function is a SQLAlchemy Session object.
    This object represents a session for interacting with the database. It allows you to query, insert,
    update, and delete data from the database using SQLAlchemy ORM
    :type db: Session
    :return: The function `view_all_delegations` returns a dictionary containing two keys:
    "sent_delegations" and "received_delegations". The values associated with these keys are lists of
    dictionaries, where each dictionary represents a delegation. The delegation data includes
    information such as manager ID, manager name, delegate manager ID, delegate manager name, date of
    delegation, updated datetime, and status of delegation for
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
