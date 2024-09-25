from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List


from ..database import get_db
from ..email.routes import send_email
from ..employees.routes import read_employee
from . import crud, schemas

router = APIRouter()


from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..email.routes import send_email
from ..employees.routes import read_employee  # Import to fetch employee info
from . import crud, schemas

router = APIRouter()


@router.post("/request")
async def create_wfh_request(
    arrangement: schemas.ArrangementCreate, db: Session = Depends(get_db)
):
    try:
        # Fetch employee information based on requester_staff_id
        employee = read_employee(arrangement.requester_staff_id, db)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Get the employee's full name for the email
        employee_full_name = f"{employee.staff_fname} {employee.staff_lname}"

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
                        f"Recurring WFH request requires the following fields to be filled: {', '.join(missing_fields)}"
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

        # Format the arrangement details for email content
        formatted_details = "\n".join(
            [
                f"Request ID: {arrangement['arrangement_id']}\n"
                f"WFH Date: {arrangement['wfh_date']}\n"
                f"Approval Status: {arrangement['approval_status']}\n"
                f"Type: {arrangement['wfh_type']}\n"
                f"Reason: {arrangement['reason_description']}\n"
                f"Batch ID: {arrangement['batch_id']}\n"
                f"Updated: {arrangement['update_datetime']}\n"
                for arrangement in response_data
            ]
        )

        # Send success notification email
        subject = "[All-In-One] Successful Creation of WFH Request"
        content = (
            f"Dear {employee_full_name},\n\n"
            f"Your WFH request has been successfully created with the following details:\n\n"
            f"{formatted_details}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

        await send_email(
            to_email=employee.email,  # Use the employee's email from the fetched data
            subject=subject,
            content=content,
        )

        return JSONResponse(
            status_code=201,
            content={
                "message": "Request submitted successfully",
                "data": response_data,
            },
        )

    except SQLAlchemyError as e:
        # Send failure notification email
        subject = "[All-In-One] Unsuccessful Creation of WFH Request"
        content = (
            f"Dear {employee_full_name},\n\n"
            f"Unfortunately, there was an error processing your WFH request. "
            f"Please try again later.\n\nError details: {str(e)}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

        await send_email(
            to_email=employee.email,  # Use the employee's email from the fetched data
            subject=subject,
            content=content,
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view", response_model=List[schemas.ArrangementLog])
def get_all_arrangements(db: Session = Depends(get_db)):
    try:
        arrangements = crud.get_all_arrangements(db)
        return arrangements
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
