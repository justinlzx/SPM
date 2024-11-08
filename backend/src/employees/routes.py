from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from .. import utils
from ..database import get_db
from ..employees.models import Employee
from ..employees.schemas import DelegateLogCreate, EmployeeBase, EmployeePeerResponse
from ..logger import logger
from . import exceptions, schemas, services
from .dataclasses import EmployeeFilters

router = APIRouter()


@router.get("/")
def get_employees(department: str | None = None, db: Session = Depends(get_db)):
    filters = EmployeeFilters(department=department)
    employees = services.get_employees(db, filters)
    return employees


@router.get(
    "/manager/peermanager/{staff_id}",
    response_model=EmployeePeerResponse,
    summary="Get reporting manager and peer employees",
)
def get_reporting_manager_and_peer_employees(staff_id: int, db: Session = Depends(get_db)):
    if staff_id == 130002:
        return EmployeePeerResponse(manager_id=None, peer_employees=[])

    try:
        # Get manager and unlocked peers
        manager, unlocked_peers = services.get_manager_by_subordinate_id(db, staff_id)

        if not manager:
            return EmployeePeerResponse(manager_id=None, peer_employees=[])

        # Convert unlocked peers to Pydantic model
        peer_employees_pydantic: List[schemas.EmployeeBase] = (
            utils.convert_model_to_pydantic_schema(unlocked_peers, schemas.EmployeeBase)
        )

        logger.info(f"Num results: {len(unlocked_peers)}")

        # Format to response model
        response = EmployeePeerResponse(
            manager_id=manager.staff_id, peer_employees=peer_employees_pydantic
        )

        return response
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{staff_id}", response_model=EmployeeBase, summary="Get a single employee by their staff ID"
)
def get_employee_by_staff_id(staff_id: int, db: Session = Depends(get_db)):
    try:
        employee = services.get_employee_by_id(db, staff_id)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/email/{email}", response_model=EmployeeBase, summary="Get a single employee by their email"
)
def get_employee_by_email(email: EmailStr, db: Session = Depends(get_db)):
    try:
        employee = services.get_employee_by_email(db, email)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/manager/employees/{staff_id}",
    response_model=List[EmployeeBase],
    summary="Get employees under a manager",
)
def get_subordinates_by_manager_id(staff_id: int, db: Session = Depends(get_db)):
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


@router.post(
    "/manager/delegate/{staff_id}",
    response_model=DelegateLogCreate,
    summary="Create a delegation from one manager to another",
)
async def delegate_manager_route(
    staff_id: int, delegate_manager_id: int, db: Session = Depends(get_db)
):
    result = await services.delegate_manager(staff_id, delegate_manager_id, db)
    if isinstance(result, str):
        # If a message is returned, it indicates an existing delegation issue
        raise HTTPException(status_code=400, detail=result)
    return result  # Return the created delegation log if successful


@router.put(
    "/manager/delegate/{staff_id}/status",
    response_model=DelegateLogCreate,
    summary="Update the status of an existing delegation",
)
async def update_delegation_status_route(
    staff_id: int,
    status: services.DelegationApprovalStatus,
    db: Session = Depends(get_db),
    description: str = Form(None),
):
    # Check if comment is required and missing for rejected status
    if status == services.DelegationApprovalStatus.reject and not description:
        raise HTTPException(status_code=400, detail="Comment is required for rejected status.")

    # Process the delegation status update
    result = await services.process_delegation_status(staff_id, status, db, description)
    if isinstance(result, str):
        # If a message is returned, it indicates an error (e.g., delegation not found)
        raise HTTPException(status_code=404, detail=result)

    return result  # Return the updated delegation log if successful


@router.put(
    "/manager/undelegate/{staff_id}",
    response_model=DelegateLogCreate,
    summary="Remove the delegation from a manager",
)
async def undelegate_manager_route(staff_id: int, db: Session = Depends(get_db)):
    result = await services.undelegate_manager(staff_id, db)
    if isinstance(result, str):
        # Handle specific error messages from the service
        status_code = 404 if "not found" in result else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result  # Return the updated delegation log if successful


@router.get("/manager/viewdelegations/{staff_id}", summary="View all delegations sent by a manager")
def view_delegations_route(staff_id: int, db: Session = Depends(get_db)):
    try:
        return services.view_delegations(staff_id, db)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred while fetching delegations."
        )


@router.get(
    "/manager/viewalldelegations/{staff_id}", summary="View all delegations received by a manager"
)
def view_all_delegations_route(staff_id: int, db: Session = Depends(get_db)):
    try:
        return services.view_all_delegations(staff_id, db)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred while fetching delegations."
        )
