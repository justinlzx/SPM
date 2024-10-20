# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from datetime import datetime
from os import getenv
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from ..arrangements import schemas as arrangement_schemas
from ..employees import models as employee_models

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
    arrangements: List[arrangement_schemas.ArrangementCreateResponse],
    event: str,
    success=True,
    error_message=None,
    manager: employee_models.Employee = None,
):
    email_list = []

    if event == "create":
        subject, content = craft_email_content(
            employee=employee,
            arrangements=arrangements,
            success=success,
            error_message=error_message,
        )
        email_list.append((employee.email, subject, content))

        if manager:
            subject, content = craft_email_content(
                employee=employee,
                arrangements=arrangements,
                success=success,
                error_message=error_message,
                is_manager=True,
                manager=manager,
            )
            email_list.append((manager.email, subject, content))

    elif event == "approve":
        subject, content = craft_approval_email_content(
            employee=employee,
            arrangement=arrangements[0],
            is_manager=True if manager else False,
            manager=manager,
        )
        email_list.append((employee.email, subject, content))

        if manager:
            subject, content = craft_approval_email_content(
                employee=employee,
                arrangement=arrangements[0],
                is_manager=True,
                manager=manager,
            )
            email_list.append((manager.email, subject, content))

    elif event == "reject":
        subject, content = craft_rejection_email_content(
            employee=employee,
            arrangement=arrangements[0],
            is_manager=True if manager else False,
            manager=manager,
        )
        email_list.append((employee.email, subject, content))

        if manager:
            subject, content = craft_rejection_email_content(
                employee=employee,
                arrangement=arrangements[0],
                is_manager=True,
                manager=manager,
            )
            email_list.append((manager.email, subject, content))

    else:
        raise ValueError(f"Invalid event: {event}")

    for email in email_list:
        await send_email(*email)

    return True


def craft_email_content(
    employee: employee_models.Employee,
    arrangements: List[arrangement_schemas.ArrangementCreateResponse],
    success=True,
    error_message=None,
    is_manager=False,
    manager: employee_models.Employee = None,
):
    """Helper function to format email content."""
    if success:
        formatted_details = "\n".join(
            [
                f"Request ID: {arrangement.arrangement_id}\n"
                f"WFH Date: {arrangement.wfh_date}\n"
                f"Approval Status: {arrangement.current_approval_status}\n"
                f"Type: {arrangement.wfh_type}\n"
                f"Reason: {arrangement.reason_description}\n"
                f"Batch ID: {arrangement.batch_id}\n"
                f"Updated: {arrangement.update_datetime}\n"
                for arrangement in arrangements
            ]
        )

        if is_manager and manager:
            subject = "[All-In-One] Your Staff Created a WFH Request"
            content = (
                f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
                f"{employee.staff_fname} {employee.staff_lname}, one of your staff members, has successfully created a WFH request with the following details:\n\n"
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


def craft_approval_email_content(
    employee: employee_models.Employee,
    arrangement: arrangement_schemas.ArrangementUpdate,
    is_manager: bool = False,
    manager: employee_models.Employee = None,
):
    """Helper function to format email content for WFH request approval."""
    formatted_details = (
        f"Request ID: {arrangement.arrangement_id}\n"
        f"WFH Date: {arrangement.wfh_date}\n"
        f"Type: {arrangement.wfh_type}\n"
        f"Reason for WFH Request: {arrangement.reason_description}\n"
        f"Batch ID: {arrangement.batch_id}\n"
        f"Updated: {arrangement.update_datetime}\n"
        # f"Approval Status: {getattr(arrangement, 'current_approval_status', 'Approved')}\n"
        f"Approval Status: Approved\n"
        # f"Approval Reason: {getattr(arrangement, 'status_reason', reason)}\n"
        f"Approval Reason: {arrangement.reason_description}\n"
    )

    if is_manager and manager:
        subject = "[All-In-One] You Have Approved a WFH Request"
        content = (
            f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
            f"You have successfully approved a WFH request for {employee.staff_fname} {employee.staff_lname} "
            f"with the following details:\n\n"
            f"{formatted_details}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )
    else:
        subject = "[All-In-One] Your WFH Request Has Been Approved"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Your WFH request has been approved with the following details:\n\n"
            f"{formatted_details}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    return subject, content


def craft_rejection_email_content(
    employee: employee_models.Employee,
    arrangement: arrangement_schemas.ArrangementCreateResponse,
    is_manager: bool = False,
    manager: employee_models.Employee = None,
):
    """Helper function to format email content for WFH request rejection."""
    formatted_details = (
        f"Request ID: {arrangement.arrangement_id}\n"
        f"WFH Date: {arrangement.wfh_date}\n"
        f"Type: {arrangement.wfh_type}\n"
        f"Reason for WFH Request: {arrangement.reason_description}\n"
        f"Batch ID: {arrangement.batch_id}\n"
        f"Updated: {arrangement.update_datetime}\n"
        f"Rejection Status: {getattr(arrangement, 'current_approval_status', 'Rejected')}\n"
        f"Rejection Reason: {arrangement.status_reason}\n"
    )

    if is_manager and manager:
        subject = "[All-In-One] You Have Rejected a WFH Request"
        content = (
            f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
            f"You have rejected a WFH request for {employee.staff_fname} {employee.staff_lname} "
            f"with the following details:\n\n"
            f"{formatted_details}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )
    else:
        subject = "[All-In-One] Your WFH Request Has Been Rejected"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Your WFH request has been rejected with the following details:\n\n"
            f"{formatted_details}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    return subject, content


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


def craft_email_content_for_delegation(
    employee: employee_models.Employee, counterpart_employee: employee_models.Employee, event: str
):
    """
    Helper function to craft email content for delegation events.

    :param employee: The employee receiving the email (could be staff or delegate).
    :param counterpart_employee: The counterpart involved in the delegation (staff or delegate).
    :param event: The event type ('delegate', 'delegated_to', 'undelegated', 'approved', 'rejected', 'withdrawn').
    :return: Tuple of (subject, content).
    """
    if event == "delegate":
        subject = "[All-In-One] You have delegated approval responsibilities"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"You have successfully delegated your approval responsibilities to "
            f"{counterpart_employee.staff_fname} {counterpart_employee.staff_lname}.\n\n"
            f"This delegation will take effect immediately upon acceptance. Any pending approvals will "
            f"be handled by {counterpart_employee.staff_fname} once they accept the delegation.\n"
            f"Delegation Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Delegated To: {counterpart_employee.staff_fname} {counterpart_employee.staff_lname}\n"
            f"Manager (You): {employee.staff_fname} {employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "delegated_to":
        subject = "[All-In-One] Approval responsibilities delegated to you"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"{counterpart_employee.staff_fname} {counterpart_employee.staff_lname} has delegated their "
            f"approval responsibilities to you.\n\n"
            f"Please log in to the portal to review and accept the delegation.\n"
            f"Once accepted, any pending approvals assigned to {counterpart_employee.staff_fname} will be routed to you.\n\n"
            f"Delegation Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Delegated By: {counterpart_employee.staff_fname} {counterpart_employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "undelegated":
        subject = "[All-In-One] Approval responsibilities undelegated"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"The delegation of approval responsibilities between you and "
            f"{counterpart_employee.staff_fname} {counterpart_employee.staff_lname} has been revoked.\n\n"
            f"All pending approvals will be reassigned to the original manager, and you no longer have the responsibility "
            f"for approvals on behalf of {counterpart_employee.staff_fname}.\n"
            f"Undelegation Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Manager: {counterpart_employee.staff_fname} {counterpart_employee.staff_lname}\n"
            f"Delegatee (You): {employee.staff_fname} {employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "approved":
        # Email to the staff who made the request
        subject = "[All-In-One] Your delegation request has been approved"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Your delegation request to {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname} has been approved.\n\n"
            f"Delegation Approval Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Delegated To: {counterpart_employee.staff_fname} {counterpart_employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "approved_for_delegate":
        # Email to the person who approved the request
        subject = "[All-In-One] You have approved a delegation request"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"You have successfully approved the delegation request for {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname}.\n\n"
            f"Delegation Approval Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Approved By: {employee.staff_fname} {employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "rejected":
        # Email to the staff who made the request
        subject = "[All-In-One] Your delegation request has been rejected"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Your delegation request to {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname} has been rejected.\n\n"
            f"Delegation Rejection Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Rejected By: {counterpart_employee.staff_fname} {counterpart_employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "rejected_for_delegate":
        # Email to the person who rejected the request
        subject = "[All-In-One] You have rejected a delegation request"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"You have successfully rejected the delegation request for {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname}.\n\n"
            f"Delegation Rejection Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Rejected By: {employee.staff_fname} {employee.staff_lname}\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "withdrawn":
        # Email to the staff member who withdrew the delegation
        subject = "[All-In-One] Your delegation has been withdrawn"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"Your delegation to {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname} has been withdrawn.\n\n"
            f"Withdrawal Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    elif event == "withdrawn_for_delegate":
        # Email to the delegate who had their delegation withdrawn
        subject = "[All-In-One] Your delegation has been withdrawn"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"The delegation assigned to you by {counterpart_employee.staff_fname} "
            f"{counterpart_employee.staff_lname} has been withdrawn.\n\n"
            f"Withdrawal Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"This email is auto-generated. Please do not reply to this email. Thank you."
        )

    else:
        raise ValueError("Invalid event type for delegation email.")

    return subject, content
