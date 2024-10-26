from datetime import datetime
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from .. import utils
from ..arrangements import models as arrangement_models
from ..database import get_db
from ..email.routes import send_email
from ..employees import services as employee_services
from ..employees.models import DelegateLog, DelegationStatus, Employee
from ..employees.schemas import DelegateLogCreate, EmployeeBase, EmployeePeerResponse
from ..notifications.email_notifications import craft_email_content_for_delegation
from . import exceptions, models, schemas, services

router = APIRouter()


@router.get("/manager/peermanager/{staff_id}", response_model=EmployeePeerResponse)
def get_reporting_manager_and_peer_employees(staff_id: int, db: Session = Depends(get_db)):
    """
    This function retrieves the reporting manager and peer employees of an employee based on their staff
    ID, handling exceptions for employee and manager not found cases.

    :param staff_id: The `staff_id` parameter in the `get_reporting_manager_and_peer_employees` function
    represents the unique identifier of an employee for whom we want to retrieve the reporting manager
    and peer employees. This parameter is used to query the database and fetch the necessary information
    about the employee, their manager, and their
    :type staff_id: int
    :param db: The `db` parameter in the `get_reporting_manager_and_peer_employees` function is of type
    `Session` and is used to interact with the database. It is passed as a dependency using
    `Depends(get_db)`, which means that it will be provided by the dependency injection system (most
    :type db: Session
    :return: The code is returning the reporting manager and peer employees of an employee identified by
    their staff_id. If the employee reports to themselves, the manager will be set to None. The response
    includes the manager's staff_id and a list of peer employees in a Pydantic model format. If the
    employee or manager is not found, a 404 HTTP exception is raised with the corresponding error
    message.
    """

    # Auto Approve for Jack Sim and Skip manager check
    if staff_id == 130002:
        return EmployeePeerResponse(manager_id=None, peer_employees=[])

    try:
        # Get manager
        manager: models.Employee = services.get_manager_by_subordinate_id(db, staff_id)

        if not manager:
            return EmployeePeerResponse(manager_id=None, peer_employees=[])

        # Get list of peer employees
        peer_employees: List[models.Employee] = services.get_subordinates_by_manager_id(
            db, manager.staff_id
        )

        # Filter out the manager from the peer employees
        peer_employees = [peer for peer in peer_employees if peer.staff_id != manager.staff_id]

        # Convert peer employees to Pydantic model
        peer_employees_pydantic: List[schemas.EmployeeBase] = (
            utils.convert_model_to_pydantic_schema(peer_employees, schemas.EmployeeBase)
        )

        print(f"Num results: {len(peer_employees)}")

        # Format to response model
        response = schemas.EmployeePeerResponse(
            manager_id=manager.staff_id, peer_employees=peer_employees_pydantic
        )

        return response
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{staff_id}", response_model=EmployeeBase)
def get_employee_by_staff_id(staff_id: int, db: Session = Depends(get_db)):
    """
    This function retrieves an employee by their staff ID from the database and returns the employee
    details in a serialized format using a Pydantic model.

    :param staff_id: The `staff_id` parameter in the `get_employee_by_staff_id` function is an integer
    representing the unique identifier of the employee that you want to retrieve from the database. This
    function is a FastAPI endpoint that handles GET requests to fetch an employee by their staff ID
    :type staff_id: int
    :param db: The `db` parameter in the `get_employee_by_staff_id` function is a dependency parameter
    that provides a database session to the function. It is of type `Session`, which is likely an
    instance of a database session class (e.g., SQLAlchemy Session) used to interact with the database
    :type db: Session
    :return: an employee object retrieved by the staff_id provided in the URL path parameter. The return
    statement returns the employee object, and the Pydantic model `EmployeeBase` will handle the
    serialization of the employee object before sending the response. If the employee is not found based
    on the staff_id provided, an HTTP 404 error will be raised with the detail message provided by the
    `Employee
    """
    try:
        employee = services.get_employee_by_id(db, staff_id)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/email/{email}", response_model=EmployeeBase)
def get_employee_by_email(email: EmailStr, db: Session = Depends(get_db)):
    """
    This function retrieves an employee by their email address from the database and returns the
    employee details if found, raising a 404 error if the employee is not found.

    :param email: The `email` parameter in the code snippet represents the email address of the employee
    that you want to retrieve from the database. It is expected to be a valid email address string
    :type email: EmailStr
    :param db: The `db` parameter in the function `get_employee_by_email` is a dependency parameter that
    represents the database session. It is of type `Session` which is typically an instance of a
    database session provided by a database ORM (Object-Relational Mapping) like SQLAlchemy. In this
    case, the
    :type db: Session
    :return: The code snippet is a FastAPI endpoint that defines a route to retrieve an employee by
    their email address from a database. When a GET request is made to "/email/{email}", the endpoint
    calls the `get_employee_by_email` function from the `services` module to fetch the employee details
    based on the provided email address. If the employee is found, the function returns the employee
    object, which is
    """
    try:
        employee = services.get_employee_by_email(db, email)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/manager/employees/{staff_id}", response_model=List[EmployeeBase])
def get_subordinates_by_manager_id(staff_id: int, db: Session = Depends(get_db)):
    """
    This function retrieves a list of employees who report to a specific manager based on their staff
    ID.

    :param staff_id: The `staff_id` parameter in the `get_subordinates_by_manager_id` function
    represents the unique identifier of a manager whose subordinates you want to retrieve. This
    parameter is used to query the database and find all employees who report to the manager identified
    by the `staff_id`
    :type staff_id: int
    :param db: The `db` parameter in the `get_subordinates_by_manager_id` function is a dependency
    parameter that represents the database session. It is used to interact with the database to retrieve
    information about employees who report to a specific manager identified by their `staff_id`. The
    `db` parameter is passed to
    :type db: Session
    :return: The function `get_subordinates_by_manager_id` returns a list of employees who report to a
    specific manager identified by their staff_id. The list of employees is converted to Pydantic models
    using the `EmployeeBase` schema before being returned. If the manager is not found, a
    `ManagerNotFoundException` exception is raised with a status code of 404 and the exception message
    as the detail.
    """
    try:
        # Get employees that report to the given employee
        employees_under_manager: List[Employee] = services.get_subordinates_by_manager_id(
            db, staff_id
        )

        # Convert the list of employees to Pydantic model
        employees_under_manager_pydantic = utils.convert_model_to_pydantic_schema(
            employees_under_manager, EmployeeBase
        )

        return employees_under_manager_pydantic
    except exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/manager/delegate/{staff_id}", response_model=DelegateLogCreate)
async def delegate_manager_route(
    staff_id: int, delegate_manager_id: int, db: Session = Depends(get_db)
):
    """
    The function `delegate_manager` delegates the approval responsibility of a manager to another staff
    member and logs the delegation in the database.

    :param staff_id: `staff_id` is the ID of the manager whose approval responsibility is being
    delegated to another staff member
    :type staff_id: int
    :param delegate_manager_id: The `delegate_manager_id` parameter in the `delegate_manager` function
    refers to the ID of the staff member to whom the approval responsibility of a manager is being
    delegated. This parameter is used to identify the delegatee who will temporarily take over the
    approval responsibilities from the manager
    :type delegate_manager_id: int
    :param db: The `db` parameter in the `delegate_manager` function is an instance of the database
    session. It is used to interact with the database to perform operations like querying, adding,
    committing, and rolling back transactions. In this case, it is being used to query the database for
    existing delegations,
    :type db: Session
    :return: The code is returning the newly created delegation log after logging the delegation in the
    `delegate_logs` table.
    """
    result = await services.delegate_manager(staff_id, delegate_manager_id, db)
    if isinstance(result, str):
        # If a message is returned, it indicates an existing delegation issue
        raise HTTPException(status_code=400, detail=result)
    return result  # Return the created delegation log if successful


# @router.put("/manager/delegate/{staff_id}/status", response_model=DelegateLogCreate)
# async def update_delegation_status_route(
#     staff_id: int, status: services.DelegationApprovalStatus, db: Session = Depends(get_db)
# ):
#     """
#     The above functions handle updating and undelegating delegation statuses, including database
#     operations and email notifications.

#     :param staff_id: The `staff_id` parameter in the provided code snippets refers to the ID of the
#     staff member (manager or delegate) whose delegation status is being updated or who is being
#     undelegated. This ID is used to fetch the relevant delegation log entry from the database for the
#     specified staff member
#     :type staff_id: int
#     :param status: The `status` parameter in the `update_delegation_status` function and
#     `undelegate_manager` function represents the status of the delegation request. It can have two
#     possible values:
#     :type status: DelegationApprovalStatus
#     :param db: The `db` parameter in the provided code snippets is an instance of the database session.
#     It is used to interact with the database to perform operations like querying, updating, and
#     committing data. The database session is typically created and managed by the ORM (Object-Relational
#     Mapping) framework being used in
#     :type db: Session
#     :return: The `update_delegation_status` function returns an updated delegation log after updating
#     the status of a delegation request (accepted or rejected).
#     """
#     result = await services.process_delegation_status(staff_id, status, db)
#     if isinstance(result, str):
#         raise HTTPException(status_code=404, detail=result)
#     return result  # Return the updated delegation log if successful


@router.put("/manager/delegate/{staff_id}/status", response_model=DelegateLogCreate)
async def update_delegation_status_route(
    staff_id: int,
    status: services.DelegationApprovalStatus,
    db: Session = Depends(get_db),
    description: str = Form(None),
):
    """
    The above functions handle updating and undelegating delegation statuses, including database
    operations and email notifications.

    :param staff_id: The `staff_id` parameter in the provided code snippets refers to the ID of the
    staff member (manager or delegate) whose delegation status is being updated or who is being
    undelegated. This ID is used to fetch the relevant delegation log entry from the database for the
    specified staff member
    :type staff_id: int
    :param status: The `status` parameter in the `update_delegation_status` function and
    `undelegate_manager` function represents the status of the delegation request. It can have two
    possible values:
    :type status: DelegationApprovalStatus
    :param db: The `db` parameter in the provided code snippets is an instance of the database session.
    It is used to interact with the database to perform operations like querying, updating, and
    committing data. The database session is typically created and managed by the ORM (Object-Relational
    Mapping) framework being used in
    :type db: Session
    :return: The `update_delegation_status` function returns an updated delegation log after updating
    the status of a delegation request (accepted or rejected).
    """
    # Check if comment is required and missing for rejected status
    if status == services.DelegationApprovalStatus.reject and not description:
        raise HTTPException(status_code=400, detail="Comment is required for rejected status.")

    # Process the delegation status update
    result = await services.process_delegation_status(staff_id, status, db, description)
    if isinstance(result, str):
        # If a message is returned, it indicates an error (e.g., delegation not found)
        raise HTTPException(status_code=404, detail=result)

    return result  # Return the updated delegation log if successful


@router.put("/manager/undelegate/{staff_id}", response_model=DelegateLogCreate)
async def undelegate_manager_route(staff_id: int, db: Session = Depends(get_db)):
    """
    This function is an API endpoint in Python that undelegates a manager's delegation and removes the
    delegate's approval rights.

    :param staff_id: The `staff_id` parameter in the `undelegate_manager_route` function represents the
    unique identifier of the manager whose delegation is being undelegated. This parameter is used to
    identify the specific manager whose delegation is being removed and whose delegate's approval rights
    are being revoked
    :type staff_id: int
    :param db: The `db` parameter in the `undelegate_manager_route` function is of type `Session` and is
    used to interact with the database. It is passed as a dependency using the `Depends` function, which
    ensures that a new database session is created and made available within the scope of the
    :type db: Session
    :return: The updated delegation log is being returned if the operation to undelegate a manager is
    successful.
    """
    result = await services.undelegate_manager(staff_id, db)
    if isinstance(result, str):
        # Handle specific error messages from the service
        status_code = 404 if "not found" in result else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result  # Return the updated delegation log if successful


@router.get("/manager/viewdelegations/{staff_id}")
def view_delegations_route(staff_id: int, db: Session = Depends(get_db)):
    """
    This Python function defines an API endpoint to view delegations sent by a manager and pending
    approval delegations.

    :param staff_id: The `staff_id` parameter in the `view_delegations_route` function represents the
    unique identifier of the staff member for whom you want to view delegations. This parameter is
    expected to be an integer value
    :type staff_id: int
    :param db: The `db` parameter in the `view_delegations_route` function is a dependency injection
    parameter that provides a database session to the route function. It is used to interact with the
    database within the route function to perform database operations like querying, updating, or
    deleting data. In this case, the
    :type db: Session
    :return: The code is returning the result of the `services.view_delegations(staff_id, db)` function
    call, which is responsible for fetching and returning delegations sent by the manager and pending
    approval delegations for a specific staff member identified by `staff_id`. If an unexpected error
    occurs during this process, a 500 status code HTTPException is raised with the detail message "An
    unexpected error occurred while
    """
    try:
        return services.view_delegations(staff_id, db)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred while fetching delegations."
        )


@router.get("/manager/viewalldelegations/{staff_id}")
def view_all_delegations_route(staff_id: int, db: Session = Depends(get_db)):
    """
    The function `view_all_delegations` retrieves and returns all delegations sent and received by a
    specified manager from the database.

    :param staff_id: The `staff_id` parameter in the `view_all_delegations` function represents the
    unique identifier of the manager for whom you want to view all delegations, whether they were sent
    or received by the manager. This ID helps identify the specific manager in the database for whom the
    delegations need to
    :type staff_id: int
    :param db: The `db` parameter in the `view_all_delegations` function represents the database
    session. It is used to interact with the database to retrieve information about delegations sent and
    received by a specified manager. The database session (`Session`) is typically created using a
    dependency function like `get_db`
    :type db: Session
    :return: The `view_all_delegations` function returns a JSON response containing two lists:
    1. `sent_delegations`: All delegations sent by the specified manager across all statuses.
    2. `received_delegations`: All delegations received by the specified manager across all statuses.
    """
    try:
        return services.view_all_delegations(staff_id, db)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred while fetching delegations."
        )
