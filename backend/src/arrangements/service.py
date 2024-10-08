from datetime import datetime, timedelta
from typing import Annotated, List

from fastapi import Depends, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .schemas import (
    ArrangementCreate,
    ArrangementCreateWithFile,
    ArrangementCreateResponse,
)
from .utils import fit_model_to_schema, upload_file, delete_file
from ..notifications.email_notifications import (
    craft_email_content,
    fetch_manager_info,
    send_email,
)

from ..database import get_db
from ..employees.routes import get_employee_by_staff_id  # Fetch employee info

from . import crud
import boto3


async def create_wfh_request(
    wfh_request: Annotated[ArrangementCreate, Form()],
    supporting_docs: List[File] = File(None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        wfh_request = ArrangementCreateWithFile.model_validate(wfh_request)
        # Fetch employee (staff) information
        staff = get_employee_by_staff_id(wfh_request.staff_id, db)
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
            manager = get_employee_by_staff_id(manager_info["manager_id"], db)

        # Upload supporting documents to S3 bucket
        s3_client = boto3.client("s3")

        file_urls = []
        try:
            for file in supporting_docs:
                response = await upload_file(
                    wfh_request.staff_id,
                    str(wfh_request.update_datetime),
                    file,
                    s3_client,
                )

                if not response:
                    raise Exception(f"Failed to upload supporting document: {file}")

                file_urls.append(response["file_url"])
        except Exception as upload_error:
            # If any upload fails, delete all uploaded files and raise an exception
            await delete_file(wfh_request.staff_id, wfh_request.update_datetime)
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading files: {str(upload_error)}",
            )

        wfh_request.supporting_doc_1 = file_urls[0] if file_urls else None
        wfh_request.supporting_doc_2 = file_urls[1] if len(file_urls) > 1 else None
        wfh_request.supporting_doc_3 = file_urls[2] if len(file_urls) > 2 else None

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
                ArrangementCreateResponse,
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
