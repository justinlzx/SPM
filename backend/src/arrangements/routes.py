from typing import Annotated, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from ..employees import exceptions as employee_exceptions
from ..employees import models as employee_models
from ..employees import services as employee_services
from ..notifications.email_notifications import craft_and_send_email
from . import schemas, services
from .exceptions import (ArrangementActionNotAllowedError,
                         ArrangementNotFoundError)

router = APIRouter()


@router.get("/{arrangement_id}", summary="Get an arrangement by its arrangement_id")
def get_arrangement_by_id(arrangement_id: int, db: Session = Depends(get_db)):
    try:
        arrangement: schemas.ArrangementResponse = services.get_arrangement_by_id(
            db, arrangement_id
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangement retrieved successfully",
                "data": {
                    **arrangement.model_dump(),
                    "update_datetime": (arrangement.update_datetime.isoformat()),
                },
            },
        )
    except ArrangementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personal/{staff_id}", summary="Get personal arrangements by an employee's staff_id")
def get_personal_arrangements_by_filter(
    staff_id: int,
    current_approval_status: List[
        Literal["pending", "approved", "rejected", "withdrawn", "cancelled"]
    ] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    try:
        arrangements: List[schemas.ArrangementResponse] = (
            services.get_personal_arrangements_by_filter(db, staff_id, current_approval_status)
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Personal arrangements retrieved successfully",
                "data": [
                    {**data.model_dump(), "update_datetime": (data.update_datetime.isoformat())}
                    for data in arrangements
                ],
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/subordinates/{manager_id}",
    summary="Get arrangements for subordinate employees under a manager",
)
def get_subordinates_arrangements(
    manager_id: int,
    current_approval_status: Optional[
        List[Literal["pending", "approved", "rejected", "withdrawn", "cancelled"]]
    ] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    try:
        arrangements: List[schemas.ArrangementResponse] = services.get_subordinates_arrangements(
            db, manager_id, current_approval_status
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements for employees under manager retrieved successfully",
                "manager_id": manager_id,
                "data": [
                    {**data.model_dump(), "update_datetime": (data.update_datetime.isoformat())}
                    for data in arrangements
                ],
            },
        )
    except employee_exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/team/{staff_id}",
    summary="Get all arrangements for a team, including peers and subordinates",
)
def get_team_arrangements(
    staff_id: int,
    current_approval_status: Optional[Literal["pending", "approved"]] = Query(
        None, description="Filter by status"
    ),
    db: Session = Depends(get_db),
):
    try:
        arrangements: Dict[str, List[schemas.ArrangementResponse]] = services.get_team_arrangements(
            db, staff_id, current_approval_status
        )
        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements for team retrieved successfully",
                "staff_id": staff_id,
                "data": {
                    key: [
                        {**data.model_dump(), "update_datetime": (data.update_datetime.isoformat())}
                        for data in value
                    ]
                    for key, value in arrangements.items()
                },
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="Create a new WFH request")
async def create_wfh_request(
    wfh_request: Annotated[schemas.ArrangementCreate, Form()],
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        # Check that employee exists
        requester_employee: employee_models.Employee = employee_services.get_employee_by_id(
            db, wfh_request.staff_id
        )

        # Fetch manager info using the helper function from notifications
        manager: employee_models.Employee = employee_services.get_manager_by_subordinate_id(
            db, wfh_request.staff_id
        )

        # Create the arrangements
        created_arrangements: List[schemas.ArrangementCreateResponse] = (
            services.create_arrangements_from_request(db, wfh_request)
        )

        # Craft and send email
        await craft_and_send_email(
            requester_employee, created_arrangements, "create", success=True, manager=manager
        )

        #auto_approved = wfh_request.current_approval_status == "approved"
        auto_approved = wfh_request.staff_id == 130002
        response_message = (
            f"Request submitted{' and auto-approved ' if auto_approved else ' '}successfully"
        )

        return JSONResponse(
            status_code=201,
            content={
                "message": response_message,
                "data": [
                    {
                        **arrangement.model_dump(),
                        "update_datetime": (arrangement.update_datetime.isoformat()),
                    }
                    for arrangement in created_arrangements
                ],
            },
        )

    except employee_exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

    # TODO: Custom exception handling for Pydantic validation errors

    except SQLAlchemyError as e:
        # Craft and send failure notification email to the employee (staff)
        craft_and_send_email(
            requester_employee, created_arrangements, "create", success=False, error_message=str(e)
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{arrangement_id}/status", summary="Update the status of a WFH request")
async def update_wfh_request(
    arrangement_id: int,
    wfh_update: Annotated[schemas.ArrangementUpdate, Form()],
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        wfh_update.arrangement_id = arrangement_id

        # Update the arrangement status
        updated_arrangement = services.update_arrangement_approval_status(db, wfh_update)

        # Fetch the staff (requester) information
        requester_employee: employee_models.Employee = employee_services.get_employee_by_id(
            db, updated_arrangement.staff_id
        )

        # Fetch manager info
        approving_officer: employee_models.Employee = employee_services.get_employee_by_id(
            db, updated_arrangement.approving_officer
        )

        # Prepare and send email to staff and approving officer
        await craft_and_send_email(
            requester_employee,
            [updated_arrangement],
            "approve",
            success=True,
            manager=approving_officer,
        )

        # Custom message based on the action performed
        action_message = {
            "approved": "Request approved successfully",
            "rejected": "Request rejected successfully",
            "withdrawn": "Request withdrawn successfully",
            "cancelled": "Request cancelled successfully",
        }.get(updated_arrangement.current_approval_status, "Request processed successfully")

        return JSONResponse(
            status_code=201,
            content={
                "message": f"{action_message} and notifications sent",
                "data": {
                    **updated_arrangement.model_dump(),
                    "update_datetime": (updated_arrangement.update_datetime.isoformat()),
                },
            },
        )

    except ArrangementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ArrangementActionNotAllowedError as e:
        raise HTTPException(status_code=406, detail=str(e))

    except SQLAlchemyError as e:
        print(f"Database error occurred: {str(e)}")  # Log the database error
        raise HTTPException(status_code=500, detail="Database error")


# =========================== DEPRECATED ENDPOINTS ===========================

# @router.get(
#     "/view/{manager_id}",
#     response_model=List[schemas.ArrangementResponse],
#     summary="Get all Pending Arrangements by Manager",
# )
# def get_arrangements_by_manager(
#     manager_id: int,
#     db: Session = Depends(get_db),
#     status: Optional[str] = Query(None, description="Filter by status"),
# ):
#     try:
#         arrangements = crud.get_arrangements_by_manager(db, manager_id, status)
#         for arrangement in arrangements:
#             print(arrangement.requester_info)
#         return arrangements
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get(
#     "/view/pending-requests/{staff_id}",
#     response_model=List[schemas.ArrangementCreateResponse],
# )
# def get_pending_requests_for_manager_and_team(staff_id: int, db: Session = Depends(get_db)):
#     """Get the pending WFH requests for the manager's employees."""
#     try:
#         currentList = []
#         # Check if the employee is a manager
#         employees_under_manager: List[Employee] = get_employees_by_manager_id(db, staff_id)

#         if not employees_under_manager:
#             # If the employee is not a manager, return a message indicating no pending requests
#             return JSONResponse(
#                 status_code=200, content={"message": "No pending requests at this time", "data":
#                   []}
#             )

#         # # If employee is manager
#         # currentList.append(staff_id)
#         for employee in employees_under_manager:
#             currentList.append(employee.staff_id)  # Access staff_id as an attribute

#         # Debug: Log the contents of currentList
#         print("Current List of Staff IDs:", currentList)

#         # Fetch all pending requests for these staff_ids
#         pending_requests = crud.get_pending_requests_by_staff_ids(db, currentList)

#         response_data = [req.__dict__ for req in pending_requests]
#         for data in response_data:
#             data.pop("_sa_instance_state", None)

#         response_data = [
#             fit_model_to_schema(
#                 data,
#                 schemas.ArrangementCreateResponse,
#                 {
#                     "requester_staff_id": "staff_id",
#                     "current_approval_status": "approval_status",
#                 },
#             )
#             for data in response_data
#         ]

#         return JSONResponse(
#             status_code=200,
#             content={
#                 "message": "Arrangements retrieved successfully",
#                 "data": [data.model_dump() for data in response_data],  # Convert to dict
#             },
#         )

#     except Exception as e:
#         print(f"An error occurred: {str(e)}")  # Log the error for debugging
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# OLD VERSION WHEREBY PEOPLE CAN VIEW THEIR OWN PENDING ARRANGEMENTS
# @router.get(
#     "/view/pending-requests/{staff_id}",
#     response_model=List[schemas.ArrangementCreateResponse],
# )
# def get_pending_requests_for_manager_and_team(staff_id: int, db: Session = Depends(get_db)):
#     """
#     Get the pending WFH requests for the manager and their employees.
#     """
#     try:
#         currentList = []
#         # Check if the employee is a manager
#         employees_under_manager: List[Employee] = get_employees_by_manager_id(db, staff_id)

#         # if not employees_under_manager:
#         #     currentList.append(staff_id)

#         # If employee is manager
#         currentList.append(staff_id)
#         for employee in employees_under_manager:
#             currentList.append(employee.staff_id)  # Access staff_id as an attribute

#         # Debug: Log the contents of currentList
#         print("Current List of Staff IDs:", currentList)

#         # Fetch all pending requests for these staff_ids
#         pending_requests = crud.get_pending_requests_by_staff_ids(db, currentList)

#         response_data = [req.__dict__ for req in pending_requests]
#         for data in response_data:
#             data.pop("_sa_instance_state", None)

#         response_data = [
#             fit_model_to_schema(
#                 data,
#                 schemas.ArrangementCreateResponse,
#                 {
#                     "requester_staff_id": "staff_id",
#                     "approval_status": "current_approval_status",
#                 },
#             )
#             for data in response_data
#         ]

#         return JSONResponse(
#             status_code=200,
#             content={
#                 "message": "Arrangements retrieved successfully",
#                 "data": [data.model_dump() for data in response_data],  # Convert to dict
#             },
#         )

#     except Exception as e:
#         print(f"An error occurred: {str(e)}")  # Log the error for debugging
#         raise HTTPException(status_code=500, detail="Internal Server Error")
