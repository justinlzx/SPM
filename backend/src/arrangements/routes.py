from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..notifications.email_notifications import (
    send_email,
    craft_email_content,
    fetch_manager_info,
)  # Import helper functions
from ..employees.routes import read_employee  # Fetch employee info
from . import crud, schemas

router = APIRouter()


@router.post("/request")
async def create_wfh_request(
    arrangement: schemas.ArrangementCreate, db: Session = Depends(get_db)
):
    try:
        # Fetch employee (staff) information
        staff = read_employee(arrangement.requester_staff_id, db)
        if not staff:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Fetch manager info using the helper function from notifications
        manager_info = await fetch_manager_info(arrangement.requester_staff_id)
        manager = None

        # Only fetch manager if manager_id is not null
        if (
            manager_info
            and manager_info["manager_id"] is not None
            and manager_info["manager_id"] != arrangement.requester_staff_id
        ):
            manager = read_employee(manager_info["manager_id"], db)

        # Handle recurring requests
        arrangement_requests = []
        if arrangement.is_recurring:
            missing_fields = [
                field
                for field in [
                    "recurring_end_date",
                    "recurring_frequency_number",
                    "recurring_frequency_unit",
                    "recurring_occurrences",
                ]
                if getattr(arrangement, field) is None
            ]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Recurring WFH request requires the following fields to be filled: "
                        f"{', '.join(missing_fields)}"
                    ),
                )

            for i in range(arrangement.recurring_occurrences):
                arrangement_copy = arrangement.model_copy()

                if arrangement.recurring_frequency_unit == "week":
                    arrangement_copy.wfh_date = (
                        datetime.strptime(arrangement.wfh_date, "%Y-%m-%d")
                        + timedelta(weeks=i * arrangement.recurring_frequency_number)
                    ).strftime("%Y-%m-%d")
                else:
                    arrangement_copy.wfh_date = (
                        datetime.strptime(arrangement.wfh_date, "%Y-%m-%d")
                        + timedelta(days=i * arrangement.recurring_frequency_number * 7)
                    ).strftime("%Y-%m-%d")

                arrangement_requests.append(arrangement_copy)
        else:
            arrangement_requests.append(arrangement)

        response_data = []

        created_arrangements = crud.create_bulk_wfh_request(db, arrangement_requests)

        response_data = [req.__dict__ for req in created_arrangements]
        for data in response_data:
            data.pop("_sa_instance_state", None)

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
                "data": response_data,
            },
        )

    except SQLAlchemyError as e:
        # Craft and send failure notification email to the employee (staff)
        subject, content = await craft_email_content(
            staff, response_data=None, success=False, error_message=str(e)
        )
        await send_email(to_email=staff.email, subject=subject, content=content)

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view", response_model=List[schemas.ArrangementLog])
def get_all_arrangements(db: Session = Depends(get_db)):
    try:
        arrangements = crud.get_all_arrangements(db)
        return arrangements
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
