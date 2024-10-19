# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from os import getenv
from typing import List, Union

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from ..arrangements import schemas as arrangement_schemas
from ..employees import models as employee_models
from . import exceptions

# from sqlalchemy.orm import Session


# from ..employees.routes import read_employee

load_dotenv()
BASE_URL = getenv("BACKEND_BASE_URL", "http://localhost:8000")


async def fetch_manager_info(staff_id: int):
    """Fetch manager information by making an HTTP request to the
    /employees/manager/peermanager/{staff_id} route."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/manager/peermanager/{staff_id}")

            # Check if the response is successful
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error fetching manager info: {response.text}",
                )

            manager_info = response.json()
            return manager_info

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching manager info: {str(exc)}",
        )


async def craft_and_send_email(
    employee: employee_models.Employee,
    arrangements: Union[
        List[arrangement_schemas.ArrangementCreateResponse], arrangement_schemas.ArrangementUpdate
    ],
    action: str,
    manager: employee_models.Employee = None,
    error_message: str = None,
):
    missing_args = []
    if not employee:
        missing_args.append("employee")
    if not arrangements:
        missing_args.append("arrangements")
    if not action:
        missing_args.append("action")

    if missing_args:
        raise TypeError(
            f"craft_email_content() missing {len(missing_args)} required positional argument(s): {', '.join(missing_args)}"
        )

    # REVIEW: should move this validation logic to the Pydantic model
    required_employee_attributes = ["staff_fname", "staff_lname", "email"]
    missing_employee_attributes = [
        attr for attr in required_employee_attributes if not getattr(employee, attr, None)
    ]
    if missing_employee_attributes:
        raise AttributeError(
            f"Employee is missing required attributes: {', '.join(missing_employee_attributes)}"
        )

    # REVIEW: should move this validation logic to the Pydantic model
    required_arrangement_attributes = [
        "arrangement_id",
        "wfh_date",
        "wfh_type",
        "batch_id",
        "current_approval_status",
        "update_datetime",
    ]
    for arrangement in arrangements:
        missing_arrangement_attributes = [
            attr for attr in required_arrangement_attributes if not getattr(arrangement, attr, None)
        ]
        if missing_arrangement_attributes:
            raise AttributeError(
                f"Arrangement is missing required attributes: {', '.join(missing_arrangement_attributes)}"
            )

    if action not in ["create", "approve", "reject"]:
        raise ValueError(f"Invalid action: {action}")

    if action in ["create", "approve", "reject"] and not manager:
        raise ValueError("Manager is required for the specified action.")

    if error_message is not None and error_message == "":
        raise ValueError("Error message cannot be an empty string.")

    if not isinstance(arrangements, List):
        arrangements = [arrangements]

    email_list = []

    email_content = craft_email_content(
        employee=employee,
        arrangements=arrangements,
        action=action,
        error_message=error_message,
        manager=manager,
    )

    if email_content.get("employee"):
        email_list.append(
            (
                employee.email,
                email_content["employee"]["subject"],
                email_content["employee"]["content"],
            )
        )
    if email_content.get("manager"):
        email_list.append(
            (
                manager.email,
                email_content["manager"]["subject"],
                email_content["manager"]["content"],
            )
        )

    email_errors = []

    for email in email_list:
        try:
            await send_email(*email)
        except HTTPException:
            email_errors.append(email[0])

    if email_errors:
        raise exceptions.EmailNotificationException(email_errors)

    return True


def craft_email_content(
    employee: employee_models.Employee,
    arrangements: Union[
        List[arrangement_schemas.ArrangementCreateResponse], arrangement_schemas.ArrangementUpdate
    ],
    action: str,
    manager: employee_models.Employee = None,
    error_message: str = None,
):
    if not isinstance(arrangements, List):
        arrangements = [arrangements]

    formatted_details = "\n".join(
        [
            f"Request ID: {arrangement.arrangement_id}\n"
            f"WFH Date: {arrangement.wfh_date}\n"
            f"Type: {arrangement.wfh_type}\n"
            f"Reason for WFH Request: {arrangement.reason_description}\n"
            f"Batch ID: {arrangement.batch_id}\n"
            f"Request Status: {arrangement.current_approval_status}\n"
            f"Updated At: {arrangement.update_datetime}\n"
            # f"Approval Reason: {arrangement.reason_description}\n"
            for arrangement in arrangements
        ]
    )

    email_subject_content = {
        "create": {
            "success": {
                "employee": {
                    "subject": "[All-In-One] Successful Creation of WFH Request",
                    "content": (
                        f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                        f"Your WFH request has been successfully created with the following details:\n\n"
                        f"{formatted_details}\n\n"
                        "This email is auto-generated. Please do not reply to this email. Thank you."
                    ),
                },
                "manager": {
                    "subject": "[All-In-One] Your Staff Created a WFH Request",
                    "content": (
                        f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
                        f"{employee.staff_fname} {employee.staff_lname}, one of your staff members, has successfully created a WFH request with the following details:\n\n"
                        f"{formatted_details}\n\n"
                        "This email is auto-generated. Please do not reply to this email. Thank you."
                    ),
                },
            },
            "failure": {
                "employee": {
                    "subject": "[All-In-One] Unsuccessful Creation of WFH Request",
                    "content": (
                        f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                        "Unfortunately, there was an error processing your WFH request. "
                        "Please try again later.\n\n"
                        f"Error details: {error_message}\n\n"
                        "This email is auto-generated. Please do not reply to this email. Thank you."
                    ),
                },
            },
        },
        "approve": {
            "employee": {
                "subject": "[All-In-One] Your WFH Request Has Been Approved",
                "content": (
                    f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                    "Your WFH request has been approved with the following details:\n\n"
                    f"{formatted_details}\n\n"
                    "This email is auto-generated. Please do not reply to this email. Thank you."
                ),
            },
            "manager": {
                "subject": "[All-In-One] You Have Approved a WFH Request",
                "content": (
                    f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
                    f"You have successfully approved a WFH request for {employee.staff_fname} {employee.staff_lname} "
                    "with the following details:\n\n"
                    f"{formatted_details}\n\n"
                    "This email is auto-generated. Please do not reply to this email. Thank you."
                ),
            },
        },
        "reject": {
            "employee": {
                "subject": "[All-In-One] Your WFH Request Has Been Rejected",
                "content": (
                    f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                    "Your WFH request has been rejected with the following details:\n\n"
                    f"{formatted_details}\n\n"
                    "This email is auto-generated. Please do not reply to this email. Thank you."
                ),
            },
            "manager": {
                "subject": "[All-In-One] You Have Rejected a WFH Request",
                "content": (
                    f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
                    f"You have rejected a WFH request for {employee.staff_fname} {employee.staff_lname} "
                    "with the following details:\n\n"
                    f"{formatted_details}\n\n"
                    "This email is auto-generated. Please do not reply to this email. Thank you."
                ),
            },
        },
    }

    result: dict = email_subject_content.get(action, None)

    if action == "create":
        result = result.get("failure") if error_message else result.get("success")

    return result


async def send_email(to_email: str, subject: str, content: str):
    """Sends an email by making a POST request to the /email/sendemail route."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/email/sendemail",  # Use the base URL from environment variables
                data={"to_email": to_email, "subject": subject, "content": content},
            )
            # Check if the response is successful
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while sending the email: {str(exc)}",
        )


# =========== DEPRECATED FUNCTIONS =============
