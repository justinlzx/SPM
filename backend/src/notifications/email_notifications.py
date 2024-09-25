import smtplib
import httpx

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..employees.routes import read_employee

load_dotenv()
BASE_URL = getenv("BACKEND_BASE_URL", "http://localhost:8000")


async def fetch_manager_info(staff_id: int):
    """
    Fetch manager information by making an HTTP request to the /employee/manager/peermanager/{staff_id} route.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/employee/manager/peermanager/{staff_id}"
            )

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


async def craft_email_content(
    employee, response_data, success=True, error_message=None, is_manager=False
):
    """
    Helper function to format email content.
    """
    if success:
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

        if is_manager:
            subject = "[All-In-One] Your Staff Created a WFH Request"
            content = (
                f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                f"One of your staff members has successfully created a WFH request with the following details:\n\n"
                f"{formatted_details}\n\n"
                f"This email is auto-generated. Please do not reply to this email. Thank you."
            )
        else:
            subject = "[All-In-One] Successful Creation of WFH Request"
            content = (
                f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
                f"Your WFH request has been successfully created with the following details:\n\n"
                f"{formatted_details}\n\n"
                f"This email is auto-generated. Please do not reply to this email. Thank you."
            )
    else:
        subject = "[All-In-One] Unsuccessful Creation of WFH Request"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Unfortunately, there was an error processing your WFH request. "
            f"Please try again later.\n\nError details: {error_message}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    return subject, content


async def send_email(to_email: str, subject: str, content: str):
    """
    Sends an email by making a POST request to the /email/sendemail route.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/email/sendemail",  # Use the base URL from environment variables
                data={"to_email": to_email, "subject": subject, "content": content},
            )
            # Check if the response is successful
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while sending the email: {str(exc)}",
        )
