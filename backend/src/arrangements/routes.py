from datetime import date, datetime
from typing import Annotated, Dict, List, Literal, Optional

from sqlalchemy import Date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from ..employees import exceptions as employee_exceptions
from ..employees import models as employee_models
from ..employees import services as employee_services
from ..logger import logger
from ..notifications import exceptions as notification_exceptions
from ..notifications.email_notifications import craft_and_send_email
from . import exceptions as arrangement_exceptions
from . import schemas, services
from .schemas import ArrangementCreate, ArrangementResponse, ArrangementUpdate

router = APIRouter()


@router.get("/{arrangement_id}", summary="Get an arrangement by its arrangement_id")
def get_arrangement_by_id(arrangement_id: int, db: Session = Depends(get_db)):
    try:
        arrangement: ArrangementResponse = services.get_arrangement_by_id(db, arrangement_id)

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
    except arrangement_exceptions as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/personal/{staff_id}",
    summary="Get personal arrangements by an employee's staff_id",
)
def get_personal_arrangements_by_filter(
    staff_id: int,
    current_approval_status: List[
        Literal[
            "pending approval",
            "pending withdrawal",
            "approved",
            "rejected",
            "withdrawn",
            "cancelled",
        ]
    ] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Fetching personal arrangements for staff ID: {staff_id}")
        arrangements: List[schemas.ArrangementResponse] = (
            services.get_personal_arrangements_by_filter(db, staff_id, current_approval_status)
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Personal arrangements retrieved successfully",
                "data": [
                    {
                        **data.model_dump(),
                        "update_datetime": (data.update_datetime.isoformat()),
                    }
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
    name: Optional[str] = Query(None, description="Name of the employee"),
    start_date: Optional[date] = Query(None, description="Start Date"),
    end_date: Optional[date] = Query(None, description="End Date"),
    wfh_type: Optional[Literal["full", "am", "pm"]] = Query(
        None, description="Type of WFH arrangement"
    ),
    current_approval_status: Optional[
        List[
            Literal[
                "pending approval",
                "pending withdrawal",
                "approved",
                "rejected",
                "withdrawn",
                "cancelled",
            ]
        ]
    ] = Query(None, description="Filter by status"),
    items_per_page: int = Query(10, description="Items per Page"),
    page_num: int = Query(1, description="Page Number"),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Fetching arrangements for employees under manager ID: {manager_id}")
        arrangements, pagination_meta = services.get_subordinates_arrangements(
            db,
            manager_id,
            current_approval_status,
            name,
            start_date,
            end_date,
            wfh_type,
            items_per_page,
            page_num,
        )

        arrangements_dict = [arrangement.model_dump() for arrangement in arrangements]

        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements for employees under manager retrieved successfully",
                "manager_id": manager_id,
                "data": arrangements_dict,
                "pagination_meta": pagination_meta,
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
    current_approval_status: Optional[
        Literal["pending approval", "pending withdrawal", "approved"]
    ] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    try:
        arrangements: Dict[str, List[ArrangementResponse]] = services.get_team_arrangements(
            db, staff_id, current_approval_status
        )
        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements for team retrieved successfully",
                "staff_id": staff_id,
                "data": {
                    key: [
                        {
                            **data.model_dump(),
                            "update_datetime": (data.update_datetime.isoformat()),
                        }
                        for data in value
                    ]
                    for key, value in arrangements.items()
                },
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request")
async def create_wfh_request(
    requester_staff_id: int = Form(..., title="Staff ID of the requester"),
    wfh_date: date = Form(..., title="Date of the WFH request"),
    wfh_type: Literal["full", "am", "pm"] = Form(..., title="Type of WFH arrangement"),
    reason_description: str = Form(..., title="Reason for requesting the WFH"),
    is_recurring: Optional[bool] = Form(
        False, title="Flag to indicate if the request is recurring"
    ),
    recurring_end_date: Optional[str] = Form(None, title="End date of a recurring WFH request"),
    recurring_frequency_number: Optional[int] = Form(
        None, title="Numerical frequency of the recurring WFH request"
    ),
    recurring_frequency_unit: Optional[Literal["week", "month"]] = Form(
        None, title="Unit of the frequency of the recurring WFH request"
    ),
    recurring_occurrences: Optional[int] = Form(
        None, title="Number of occurrences of the recurring WFH request"
    ),
    batch_id: Optional[int] = Form(None, title="Unique identifier for the batch, if any"),
    supporting_docs: Annotated[Optional[list[UploadFile]], File(upload_multiple=True)] = [],
    db: Session = Depends(get_db),
):

    update_datetime = datetime.now()
    current_approval_status = "pending approval"

    wfh_request: ArrangementCreate = {
        "reason_description": reason_description,
        "is_recurring": is_recurring,
        "recurring_end_date": recurring_end_date,
        "recurring_frequency_number": recurring_frequency_number,
        "recurring_frequency_unit": recurring_frequency_unit,
        "recurring_occurrences": recurring_occurrences,
        "batch_id": batch_id,
        "update_datetime": update_datetime,
        "current_approval_status": current_approval_status,
        "wfh_date": wfh_date,
        "wfh_type": wfh_type,
        "staff_id": requester_staff_id,
        "approving_officer": None,
    }

    return await services.create_arrangements_from_request(db, wfh_request, supporting_docs)


@router.put("/{arrangement_id}/status", summary="Update the status of a WFH request")
async def update_wfh_request(
    arrangement_id: int,
    wfh_update: Annotated[ArrangementUpdate, Form()],
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        wfh_update.arrangement_id = arrangement_id

        # Update the arrangement status
        updated_arrangement: schemas.ArrangementUpdate = (
            services.update_arrangement_approval_status(db, wfh_update)
        )

        # **Skip employee lookups for 'withdraw' and 'cancel' actions**
        if updated_arrangement.current_approval_status not in [
            "withdrawn",
            "cancelled",
        ]:
            # Fetch the staff (requester) information
            requester_employee: employee_models.Employee = employee_services.get_employee_by_id(
                db, updated_arrangement.staff_id
            )

            # Fetch manager info (approving officer)
            approving_officer: employee_models.Employee = employee_services.get_employee_by_id(
                db, updated_arrangement.approving_officer
            )

            # Prepare and send email to staff and approving officer
            await craft_and_send_email(
                employee=requester_employee,
                arrangements=updated_arrangement,
                action=wfh_update.action,
                manager=approving_officer,
            )

        # Custom message based on the action performed
        action_message = {
            "approved": "Request approved successfully",
            "rejected": "Request rejected successfully",
            "withdrawn": "Request withdrawn successfully",
            "cancelled": "Request cancelled successfully",
        }.get(
            updated_arrangement.current_approval_status,
            "Request processed successfully",
        )

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

    except arrangement_exceptions.ArrangementNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

    except arrangement_exceptions.ArrangementActionNotAllowedException as e:
        raise HTTPException(status_code=406, detail=str(e))

    except notification_exceptions.EmailNotificationException as e:
        raise HTTPException(status_code=500, detail=str(e))

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")  # Log the database error
        raise HTTPException(status_code=500, detail="Database error")


# =========================== DEPRECATED ENDPOINTS ===========================

# @router.get(
#     "/view/{manager_id}",
#     response_model=List[ArrangementResponse],
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
#     response_model=List[ArrangementCreateResponse],
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
#                 ArrangementCreateResponse,
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
#     response_model=List[ArrangementCreateResponse],
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
#                 ArrangementCreateResponse,
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
