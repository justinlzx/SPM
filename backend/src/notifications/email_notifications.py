# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from datetime import datetime
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
        List[arrangement_schemas.ArrangementCreateResponse],
        arrangement_schemas.ArrangementUpdate,
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

    if action not in [
        "create",
        "approve",
        "reject",
        "withdraw",
        "allow withdraw",
        "reject withdraw",
        "cancel",
    ]:
        raise ValueError(f"Invalid action: {action}")

    if (
        action
        in [
            "create",
            "approve",
            "reject",
            "withdraw",
            "allow withdraw",
            "reject withdraw",
            "cancel",
        ]
        and not manager
    ):
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


def format_details(
    arrangements: Union[
        List[arrangement_schemas.ArrangementCreateResponse],
        arrangement_schemas.ArrangementUpdate,
    ]
):
    return "\n".join(
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


def format_email_subject(action_statement: str):
    return f"[All-In-One] {action_statement}"


def format_email_body(
    employee: employee_models.Employee,
    action_statement: str,
    formatted_details: str,
):
    body = f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
    body += f"{action_statement} with the following details:\n\n"
    body += formatted_details
    body += "\n\nThis email is auto-generated. Please do not reply to this email. Thank you."
    return body


def craft_email_content(
    employee: employee_models.Employee,
    arrangements: Union[
        List[arrangement_schemas.ArrangementCreateResponse],
        arrangement_schemas.ArrangementUpdate,
    ],
    action: str,
    manager: employee_models.Employee = None,
    error_message: str = None,
):
    formatted_details = format_details(arrangements)

    action_statements_dict = {
        "employee": {
            "subject": {
                "create": "Successful Creation of WFH Request",
                "approve": "Your WFH Request Has Been Approved",
                "reject": "Your WFH Request Has Been Rejected",
                "withdraw": "You Have Requested to Withdraw Your WFH",
                "allow withdraw": "Your WFH Request Has Been Withdrawn",
                "reject withdraw": "Your WFH Request Withdrawal Has Been Rejected",
                "cancel": "Your WFH Request Has Been Cancelled",
            },
            "body": {
                "create": "Your WFH request has been successfully created with the following details:",
                "approve": "Your WFH request has been approved with the following details:",
                "reject": "Your WFH request has been rejected with the following details:",
                "withdraw": "Your WFH request is pending withdrawal with the following details:",
                "allow withdraw": "Your WFH request has been withdrawn with the following details:",
                "reject withdraw": "Your WFH request withdrawal has been rejected with the following details:",
                "cancel": "Your WFH request has been cancelled with the following details:",
            },
        },
        "manager": {
            "subject": {
                "create": "Your Staff Created a WFH Request",
                "approve": "You Have Approved a WFH Request",
                "reject": "You Have Rejected a WFH Request",
                "withdraw": "Your Staff Has Requested to Withdraw Their WFH",
                "allow withdraw": "You Have Approved a WFH Request Withdrawal",
                "reject withdraw": "You Have Rejected a WFH Request Withdrawal",
                "cancel": "You Have Cancelled a WFH Request",
            },
            "body": {
                "create": "One of your staff members has successfully created a WFH request with the following details:",
                "approve": "You have successfully approved a WFH request for",
                "reject": "You have rejected a WFH request for",
                "withdraw": "has request to withdraw their WFH with the following details:",
                "allow withdraw": "You have withdrawn a WFH request for",
                "reject withdraw": "You have rejected a WFH request withdrawal for",
                "cancel": "You have cancelled a WFH request for",
            },
        },
    }

    result = {
        "employee": {
            "subject": format_email_subject(action_statements_dict["employee"]["subject"][action]),
            "content": format_email_body(
                employee,
                action_statements_dict["employee"]["subject"][action],
                formatted_details,
            ),
        },
        "manager": {
            "subject": format_email_subject(action_statements_dict["manager"]["subject"][action]),
            "content": format_email_body(
                manager,
                action_statements_dict["manager"]["subject"][action],
                formatted_details,
            ),
        },
    }

    # TODO: Handle failed actions
    # if action == "create":
    #     result = result.get("failure") if error_message else result.get("success")

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


def craft_email_content_for_delegation(
    employee: employee_models.Employee,
    counterpart_employee: employee_models.Employee,
    event: str,
):
    """Helper function to craft email content for delegation events.

    :param employee: The employee receiving the email (could be staff or delegate).
    :param counterpart_employee: The counterpart involved in the delegation (staff or delegate).
    :param event: The event type ('delegate', 'delegated_to', 'undelegated', 'approved', 'rejected',
        'withdrawn').
    :return: Tuple of (subject, content).
    """
    if event == "delegate":
        subject = "[All-In-One] You have delegated approval responsibilities"
        content = (
            f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
            f"You have delegated your approval responsibilities to "
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
