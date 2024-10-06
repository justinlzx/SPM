from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from ..employees.routes import read_employee  # Fetch employee info
from ..employees.models import Employee, get_employees_by_manager_id
from ..notifications.email_notifications import (  # Import helper functions
    craft_email_content,
    craft_approval_email_content,
    craft_rejection_email_content,
    fetch_manager_info,
    send_email,
)
from . import crud, schemas
from .exceptions import ArrangementActionNotAllowedError, ArrangementNotFoundError
from .utils import fit_model_to_schema

router = APIRouter()


@router.post("/request")
async def create_wfh_request(
    wfh_request: Annotated[schemas.ArrangementCreate, Form()],
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        # Fetch employee (staff) information
        staff = read_employee(wfh_request.staff_id, db)
        if not staff:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Fetch manager info using the helper function from notifications
        manager_info = await fetch_manager_info(wfh_request.staff_id)
        manager = None

        # Only fetch manager if manager_id is not null
        if (
            manager_info
            and manager_info["manager_id"] is not None
            and manager_info["manager_id"] != wfh_request.staff_id
        ):
            manager = read_employee(manager_info["manager_id"], db)

        # Handle recurring requests
        if wfh_request.is_recurring:
            missing_fields = [
                field
                for field in [
                    "recurring_end_date",
                    "recurring_frequency_number",
                    "recurring_frequency_unit",
                    "recurring_occurrences",
                ]
                if getattr(wfh_request, field) is None
            ]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Recurring WFH request requires the following fields to be filled: "
                        f"{', '.join(missing_fields)}"
                    ),
                )

            batch = crud.create_recurring_request(db, wfh_request)
            wfh_request.batch_id = batch.batch_id

            arrangements_list = []

            for i in range(wfh_request.recurring_occurrences):
                arrangement_copy = wfh_request.model_copy()

                if wfh_request.recurring_frequency_unit == "week":
                    arrangement_copy.wfh_date = (
                        datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                        + timedelta(weeks=i * wfh_request.recurring_frequency_number)
                    ).strftime("%Y-%m-%d")
                else:
                    arrangement_copy.wfh_date = (
                        datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                        + timedelta(days=i * wfh_request.recurring_frequency_number * 7)
                    ).strftime("%Y-%m-%d")

                arrangements_list.append(arrangement_copy)
        else:
            arrangements_list = [wfh_request]

        created_arrangements = crud.create_arrangements(db, arrangements_list)

        response_data = [req.__dict__ for req in created_arrangements]
        for data in response_data:
            data.pop("_sa_instance_state", None)
        response_data = [
            fit_model_to_schema(
                data,
                schemas.ArrangementCreateResponse,
                {
                    "requester_staff_id": "staff_id",
                    "approval_status": "current_approval_status",
                },
            )
            for data in response_data
        ]

        # Craft and send success notification email to the employee (staff)
        subject, content = await craft_email_content(staff, response_data, success=True)
        await send_email(to_email=staff.email, subject=subject, content=content)

        # Only send notification to the manager if the manager_id is not null
        if manager:
            subject, content = await craft_email_content(
                staff, response_data, success=True, is_manager=True, manager=manager
            )
            await send_email(to_email=manager.email, subject=subject, content=content)

        return JSONResponse(
            status_code=201,
            content={
                "message": "Request submitted successfully",
                "data": [
                    {
                        **data.model_dump(),
                        "update_datetime": (data.update_datetime.isoformat()),
                    }
                    for data in response_data
                ],
            },
        )

    except SQLAlchemyError as e:
        # Craft and send failure notification email to the employee (staff)
        subject, content = await craft_email_content(
            staff, response_data=None, success=False, error_message=str(e)
        )
        await send_email(to_email=staff.email, subject=subject, content=content)

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request/approve")
async def approve_wfh_request(
    arrangement_id: int = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        # Update the arrangement status
        arrangement = crud.update_arrangement_approval_status(db, arrangement_id, "approve", reason)

        # Fetch the staff (requester) information
        staff = read_employee(arrangement.requester_staff_id, db)
        if not staff:
            raise HTTPException(status_code=404, detail="Employee not found")

        # # Fetch manager info
        # manager_info = await fetch_manager_info(staff.staff_id)
        # manager = None
        # if manager_info and manager_info["manager_id"] is not None:
        #     manager = read_employee(manager_info["manager_id"], db)

        # # Prepare and send email to staff
        # subject, content = await craft_approval_email_content(staff, arrangement, reason)
        # await send_email(to_email=staff.email, subject=subject, content=content)

        # # Prepare and send email to manager
        # if manager:
        #     subject, content = await craft_approval_email_content(
        #         staff, arrangement, reason, is_manager=True, manager=manager
        #     )
        #     await send_email(to_email=manager.email, subject=subject, content=content)

        return JSONResponse(
            status_code=200,
            content={"message": "Request approved successfully and notifications sent"},
        )

    except ArrangementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ArrangementActionNotAllowedError as e:
        raise HTTPException(status_code=406, detail=str(e))

    except SQLAlchemyError as e:
        print(f"Database error occurred: {str(e)}")  # Log the database error
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")  # Log any other unexpected error
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/request/reject")
async def reject_wfh_request(
    arrangement_id: int = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        # Debugging: print the received payload
        # print(f"Received payload: arrangement_id={arrangement_id}, reason={reason}")

        # Update the arrangement status
        arrangement = crud.update_arrangement_approval_status(db, arrangement_id, "reject", reason)

        # Fetch the staff (requester) information
        staff = read_employee(arrangement.requester_staff_id, db)
        if not staff:
            raise HTTPException(status_code=404, detail="Employee not found")

        # print("The staff is found")

        # EMAIL FUNCTION THROWING ERROR 500
        # # Fetch manager info
        # manager_info = await fetch_manager_info(staff.staff_id)
        # manager = None
        # if manager_info and manager_info["manager_id"] is not None:
        #     manager = read_employee(manager_info["manager_id"], db)
        #     print("The manager is found")

        # # Prepare and send email to staff
        # subject, content = await craft_rejection_email_content(staff, arrangement, reason)
        # await send_email(to_email=staff.email, subject=subject, content=content)

        # # Prepare and send email to manager
        # if manager:
        #     subject, content = await craft_rejection_email_content(
        #         staff, arrangement, reason, is_manager=True, manager=manager
        #     )
        #     await send_email(to_email=manager.email, subject=subject, content=content)

        return JSONResponse(
            status_code=200,
            content={"message": "Request rejected successfully and notifications sent"},
        )

    except ArrangementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ArrangementActionNotAllowedError as e:
        raise HTTPException(status_code=406, detail=str(e))

    except SQLAlchemyError as e:
        print(f"Database error occurred: {str(e)}")  # Log the database error
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")  # Log any other unexpected error
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/view", response_model=List[schemas.ArrangementCreateResponse])
def get_all_arrangements(db: Session = Depends(get_db)):
    try:
        arrangements = crud.get_all_arrangements(db)
        response_data = [req.__dict__ for req in arrangements]
        for data in response_data:
            data.pop("_sa_instance_state", None)
        response_data = [
            fit_model_to_schema(
                data,
                schemas.ArrangementCreateResponse,
                {
                    "requester_staff_id": "staff_id",
                    "approval_status": "current_approval_status",
                },
            )
            for data in response_data
        ]
        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements retrieved successfully",
                "data": [{**data.model_dump()} for data in response_data],
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/view/{manager_id}",
    response_model=List[schemas.ArrangementResponse],
    summary="Get all Pending Arrangements by Manager",
)
def get_arrangements_by_manager(
    manager_id: int,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    try:
        arrangements = crud.get_arrangements_by_manager(db, manager_id, status)
        for arrangement in arrangements:
            print(arrangement.requester_info)
        return arrangements
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/view/pending-requests/{staff_id}",
    response_model=List[schemas.ArrangementCreateResponse],
)
def get_pending_requests_for_manager_and_team(staff_id: int, db: Session = Depends(get_db)):
    """
    Get the pending WFH requests for the manager's employees.
    """
    try:
        currentList = []
        # Check if the employee is a manager
        employees_under_manager: List[Employee] = get_employees_by_manager_id(db, staff_id)

        if not employees_under_manager:
            # If the employee is not a manager, return a message indicating no pending requests
            return JSONResponse(
                status_code=200, content={"message": "No pending requests at this time", "data": []}
            )

        # # If employee is manager
        # currentList.append(staff_id)
        for employee in employees_under_manager:
            currentList.append(employee.staff_id)  # Access staff_id as an attribute

        # Debug: Log the contents of currentList
        print("Current List of Staff IDs:", currentList)

        # Fetch all pending requests for these staff_ids
        pending_requests = crud.get_pending_requests_by_staff_ids(db, currentList)

        response_data = [req.__dict__ for req in pending_requests]
        for data in response_data:
            data.pop("_sa_instance_state", None)

        response_data = [
            fit_model_to_schema(
                data,
                schemas.ArrangementCreateResponse,
                {
                    "requester_staff_id": "staff_id",
                    "approval_status": "current_approval_status",
                },
            )
            for data in response_data
        ]

        return JSONResponse(
            status_code=200,
            content={
                "message": "Arrangements retrieved successfully",
                "data": [data.model_dump() for data in response_data],  # Convert to dict
            },
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
