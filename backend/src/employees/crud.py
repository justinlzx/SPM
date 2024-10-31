from datetime import datetime
from typing import List

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..arrangements.commons.enums import ApprovalStatus
from ..arrangements.commons.models import LatestArrangement
from . import models
from .models import DelegateLog, DelegationStatus, Employee


def get_employee_by_staff_id(db: Session, staff_id: int) -> models.Employee:
    """This function retrieves an employee from the database based on their staff ID.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows you to interact with the database. It is used to query the database for the
    employee with the specified `staff_id`
    :type db: Session
    :param staff_id: Staff ID is a unique identifier assigned to an employee within an organization. It
    is used to distinguish one employee from another and is often used for various purposes such as
    payroll, attendance tracking, and employee records management
    :type staff_id: int
    :return: An employee object with the specified staff ID is being returned.
    """
    return db.query(models.Employee).filter(models.Employee.staff_id == staff_id).first()


def get_employee_by_email(db: Session, email: str) -> models.Employee:
    """This function retrieves an employee from the database based on their email address.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows you to interact with the database. It is used to query the database for the
    employee with the specified email address
    :type db: Session
    :param email: The `email` parameter is a string that represents the email address of the employee
    you are trying to retrieve from the database
    :type email: str
    :return: The function `get_employee_by_email` is returning an instance of the `Employee` model from
    the database that matches the provided email address after converting both email addresses to
    lowercase for case-insensitive comparison.
    """
    return db.query(models.Employee).filter(func.lower(models.Employee.email) == email).first()


def get_subordinates_by_manager_id(db: Session, manager_id: int) -> List[models.Employee]:
    """
    The function `get_subordinates_by_manager_id` retrieves a list of employees who report to a specific
    manager based on the manager's ID.

    :param db: Session object from SQLAlchemy, used for database operations
    :type db: Session
    :param manager_id: The `manager_id` parameter is an integer that represents the unique identifier of
    a manager in the database. This function retrieves a list of employees who report to the manager
    with the specified `manager_id`
    :type manager_id: int
    :return: A list of Employee objects who have the specified manager_id as their reporting manager.
    """
    return db.query(models.Employee).filter(models.Employee.reporting_manager == manager_id).all()


def get_existing_delegation(db: Session, staff_id: int, delegate_manager_id: int):
    """This function retrieves an existing delegation log entry based on the provided staff and
    delegate manager IDs.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows interaction with the database. It is used to query the database for existing
    delegation records
    :type db: Session
    :param staff_id: The `staff_id` parameter is the ID of the staff member who is delegating their
    responsibilities to another manager
    :type staff_id: int
    :param delegate_manager_id: The `delegate_manager_id` parameter in the `get_existing_delegation`
    function represents the ID of the manager who is being delegated to perform certain tasks or
    responsibilities on behalf of another manager (specified by `staff_id`). This function queries the
    database to retrieve any existing delegation logs where either the `staff
    :type delegate_manager_id: int
    :return: The function `get_existing_delegation` is returning the first instance of `DelegateLog`
    from the database where either the `manager_id` matches the `staff_id` or the `delegate_manager_id`
    matches the `delegate_manager_id`, and the `status_of_delegation` is either 'pending' or 'accepted'.
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
    The function `create_delegation` creates a new delegation log entry in a database with specified
    manager and delegate manager IDs.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows interaction with the database. It is used to add, commit, and refresh the new
    delegation record in the database
    :type db: Session
    :param staff_id: The `staff_id` parameter represents the ID of the staff member who is delegating
    their responsibilities to another staff member
    :type staff_id: int
    :param delegate_manager_id: The `delegate_manager_id` parameter in the `create_delegation` function
    refers to the unique identifier of the manager to whom the delegation is being assigned. This
    parameter is used to specify which manager will be responsible for the delegated tasks or
    responsibilities
    :type delegate_manager_id: int
    :return: The function `create_delegation` returns the newly created delegation record after adding
    it to the database, committing the changes, and refreshing the object.
    """
    existing_delegation = get_existing_delegation(db, staff_id, delegate_manager_id)
    if existing_delegation:
        return existing_delegation  # Prevent duplicate
    # Proceed to create a new delegation if none exists
    new_delegation = DelegateLog(
        manager_id=staff_id,
        delegate_manager_id=delegate_manager_id,
        date_of_delegation=datetime.utcnow(),
        status_of_delegation=DelegationStatus.pending,
    )
    db.add(new_delegation)
    db.commit()
    db.refresh(new_delegation)
    return new_delegation


def get_delegation_log_by_delegate(db: Session, staff_id: int):
    """This function retrieves a delegation log entry based on the delegate manager's staff ID.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows interaction with the database. It is used to query the database for delegate
    logs
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
    staff member who is a delegate manager. This parameter is used to filter and retrieve delegation
    logs associated with this specific staff member from the database
    :type staff_id: int
    :return: The function `get_delegation_log_by_delegate` returns the first `DelegateLog` object from
    the database where the `delegate_manager_id` matches the provided `staff_id`.
    """
    return (
        db.query(models.DelegateLog)
        .filter(models.DelegateLog.delegate_manager_id == staff_id)
        .filter(models.DelegateLog.status_of_delegation == DelegationStatus.pending)
        .first()
    )


def update_delegation_status(
    db: Session, delegation_log: DelegateLog, status: DelegationStatus, description: str = None
):
    """This Python function updates the status and description of a delegation log in a database
    session.

    :param db: The `db` parameter is of type `Session`, which is likely referring to a database session
    object used for interacting with the database. This parameter is used to perform database operations
    like committing changes and refreshing the delegation log object
    :type db: Session
    :param delegation_log: DelegateLog object representing a delegation log entry in the database
    :type delegation_log: DelegateLog
    :param status: The `status` parameter in the `update_delegation_status` function is of type
    `DelegationStatus`. It is used to update the status of a delegation log entry
    :type status: DelegationStatus
    :param description: The `description` parameter in the `update_delegation_status` function is an
    optional parameter that allows you to provide additional information or details related to the
    delegation status update. If a description is provided, it will be added to the `delegation_log` to
    provide more context or explanation for the status
    :type description: str
    :return: The function `update_delegation_status` is returning the updated `delegation_log` object
    after updating its status and description (if provided) in the database.
    """
    delegation_log.status_of_delegation = status
    if description:
        delegation_log.description = description  # Add description to the log
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def update_pending_arrangements_for_delegate(
    db: Session, manager_id: int, delegate_manager_id: int
):
    """The function updates the delegate approving officer for pending arrangements in a database.

    :param db: The `db` parameter is an instance of a database session that is used to interact with the
    database. It allows you to query, update, and commit changes to the database. In this case, it is
    being used to query the `LatestArrangement` table and update the pending arrangements for a
    :type db: Session
    :param manager_id: The `manager_id` parameter represents the ID of the manager whose pending
    arrangements need to be updated
    :type manager_id: int
    :param delegate_manager_id: The `delegate_manager_id` parameter in the
    `update_pending_arrangements_for_delegate` function represents the ID of the manager to whom the
    approval authority is being delegated. This function is designed to update the pending arrangements
    in the database for a specific manager by reassigning the approval authority to another manager
    :type delegate_manager_id: int
    """
    pending_arrangements = (
        db.query(LatestArrangement)
        .filter(
            LatestArrangement.approving_officer == manager_id,
            LatestArrangement.current_approval_status.in_(
                [ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.PENDING_WITHDRAWAL]
            ),
        )
        .all()
    )

    for arrangement in pending_arrangements:
        arrangement.delegate_approving_officer = delegate_manager_id
        db.add(arrangement)

    db.commit()


def get_delegation_log_by_manager(db: Session, staff_id: int):
    """This function retrieves a delegation log entry by manager ID from the database.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows interaction with the database. It is used to query the database for delegation
    logs
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
    staff member or manager in the database. This parameter is used to filter and retrieve delegation
    logs associated with a specific manager based on their ID
    :type staff_id: int
    :return: The function `get_delegation_log_by_manager` returns the first delegation log entry from
    the database where the manager_id matches the provided staff_id.
    """
    return db.query(models.DelegateLog).filter(models.DelegateLog.manager_id == staff_id).first()


def remove_delegate_from_arrangements(db: Session, delegate_manager_id: int):
    """This function removes a delegate manager from pending arrangements in a database.

    :param db: The `db` parameter is of type `Session`, which is likely referring to a database session
    object used for interacting with the database. It is commonly used in SQLAlchemy to perform database
    operations
    :type db: Session
    :param delegate_manager_id: The `delegate_manager_id` parameter is the unique identifier of the
    delegate manager whose approval is pending in the arrangements. This function is designed to remove
    the delegate manager from all pending arrangements where they are the approving officer
    :type delegate_manager_id: int
    """
    # pending_arrangements = (
    #     db.query(LatestArrangement)
    #     .filter(
    #         LatestArrangement.delegate_approving_officer == delegate_manager_id,
    #         LatestArrangement.current_approval_status.in_(
    #             [ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.PENDING_WITHDRAWAL]
    #         ),
    #     )
    #     .all()
    # )

    # for arrangement in pending_arrangements:
    #     arrangement.delegate_approving_officer = None  # Remove the delegate manager
    #     db.add(arrangement)
    db.query(LatestArrangement).filter(
        LatestArrangement.delegate_approving_officer == delegate_manager_id,
        LatestArrangement.current_approval_status.in_(
            [ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.PENDING_WITHDRAWAL]
        ),
    ).update({LatestArrangement.delegate_approving_officer: None}, synchronize_session=False)

    db.commit()


def mark_delegation_as_undelegated(db: Session, delegation_log: models.DelegateLog):
    """
    The function `mark_delegation_as_undelegated` updates the status of a delegation log to
    "undelegated" in the database.

    :param db: The `db` parameter is of type `Session`, which likely refers to a database session object
    used for interacting with the database. It is commonly used in SQLAlchemy to perform database
    operations
    :type db: Session
    :param delegation_log: The `delegation_log` parameter is an instance of the `DelegateLog` model
    class, which likely represents a log entry for a delegation action in a system. The function
    `mark_delegation_as_undelegated` takes this log entry and updates its `status_of_delegation`
    attribute to
    :type delegation_log: models.DelegateLog
    :return: the `delegation_log` object after marking the delegation status as undelegated in the
    database, committing the changes, and refreshing the object from the database.
    """
    delegation_log.status_of_delegation = models.DelegationStatus.undelegated
    db.commit()
    db.refresh(delegation_log)
    return delegation_log


def get_sent_delegations(db: Session, staff_id: int):
    """This function retrieves delegation logs from the database for a specific staff member based
    on their ID.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows you to interact with the database. It is used to query the database for delegate
    logs
    :type db: Session
    :param staff_id: The `get_sent_delegations` function takes two parameters:
    :type staff_id: int
    :return: This function returns a list of delegate logs from the database where the manager_id
    matches the provided staff_id and the status of delegation is either pending or accepted.
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
    """This function retrieves pending and accepted delegation logs for a specific staff member from
    the database.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows you to interact with the database. It is used to query the database for delegate
    logs
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer representing the unique identifier of a
    staff member. This identifier is used to filter and retrieve pending or accepted delegation logs
    associated with this staff member as a delegate manager
    :type staff_id: int
    :return: This function returns a list of delegate logs from the database where the delegate manager
    ID matches the provided staff ID and the status of the delegation is either 'pending' or 'accepted'.
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


def get_all_sent_delegations(db: Session, staff_id: int):
    """This function retrieves all delegation logs associated with a specific staff member from the
    database.

    :param db: The `db` parameter is of type `Session`, which is likely an instance of a database
    session that allows you to interact with the database. It is used to query the database for delegate
    logs
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
    staff member in the database. This identifier is used to filter and retrieve all delegation logs
    associated with this staff member
    :type staff_id: int
    :return: A list of all delegation logs where the manager_id matches the provided staff_id.
    """
    return db.query(DelegateLog).filter(DelegateLog.manager_id == staff_id).all()


def get_all_received_delegations(db: Session, staff_id: int):
    """This function retrieves all received delegations for a specific staff member from the
    database.

    :param db: Session object from SQLAlchemy, used to interact with the database
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of a
    staff member in the database. This identifier is used to filter and retrieve all received
    delegations associated with this staff member from the `DelegateLog` table in the database
    :type staff_id: int
    :return: The function `get_all_received_delegations` returns all `DelegateLog` entries from the
    database where the `delegate_manager_id` matches the provided `staff_id`.
    """
    return db.query(DelegateLog).filter(DelegateLog.delegate_manager_id == staff_id).all()


def get_employee_full_name(db: Session, staff_id: int):
    """This function retrieves the full name of an employee from a database based on their staff ID.

    :param db: Session object from SQLAlchemy, used to interact with the database
    :type db: Session
    :param staff_id: The `staff_id` parameter is an integer that represents the unique identifier of an
    employee in the database. It is used to query the database and retrieve the employee's full name by
    concatenating their first name (`staff_fname`) and last name (`staff_lname`). If the employee with
    the specified `
    :type staff_id: int
    :return: the full name of an employee with the given staff_id if the employee exists in the
    database. If the employee is found, it returns the concatenation of the employee's first name
    (staff_fname) and last name (staff_lname). If the employee is not found, it returns "Unknown".
    """
    employee = db.query(Employee).filter(Employee.staff_id == staff_id).first()
    return f"{employee.staff_fname} {employee.staff_lname}" if employee else "Unknown"


def get_manager_of_employee(db: Session, emp: Employee) -> Employee:
    """
    The function `get_manager_of_employee` retrieves the manager of a given employee from a database
    session.

    :param db: Session object representing the database session
    :type db: Session
    :param emp: Employee object representing the employee for whom we want to find the manager
    :type emp: Employee
    :return: the manager of the employee if the employee has a manager and the manager's staff ID is not
    the same as the employee's staff ID. If these conditions are met, the function returns the manager;
    otherwise, it returns None.
    """
    if emp.manager and emp.manager.staff_id != emp.staff_id:
        return emp.manager
    return None


def get_peer_employees(db: Session, manager_id: int) -> list[Employee]:
    """This function retrieves a list of employees who report to a specific manager from a database
    session.

    :param db: Session object for database connection
    :type db: Session
    :param manager_id: The `manager_id` parameter is an integer that represents the unique identifier of
    a manager in the database. This function `get_peer_employees` takes this `manager_id` as input and
    retrieves a list of employees who report to the specified manager
    :type manager_id: int
    :return: A list of Employee objects whose reporting manager matches the provided manager_id.
    """
    return db.query(Employee).filter(Employee.reporting_manager == manager_id).all()


def is_employee_locked_in_delegation(db: Session, employee_id: int) -> bool:
    """The function checks if an employee is currently locked in a delegation based on their ID in a
    database session.

    :param db: The `db` parameter is of type `Session`, which is likely referring to a database session
    object used in SQLAlchemy for interacting with the database. This session object is used to query
    the database for information related to employee delegation logs
    :type db: Session
    :param employee_id: The function `is_employee_locked_in_delegation` takes two parameters:
    :type employee_id: int
    :return: The function `is_employee_locked_in_delegation` returns a boolean value indicating whether
    the employee with the given `employee_id` is currently locked in a delegation process. If there is
    at least one `DelegateLog` record in the database where the employee is either the manager or the
    delegate manager, and the status of the delegation is either 'pending' or 'accepted', then the
    function returns `True
    """
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
