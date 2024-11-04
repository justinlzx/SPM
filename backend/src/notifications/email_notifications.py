# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from datetime import datetime
from os import getenv
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from ..arrangements.commons.dataclasses import ArrangementResponse
from ..arrangements.commons.enums import Action, ApprovalStatus
from ..employees import models as employee_models
from ..logger import logger
from . import exceptions

load_dotenv()
BASE_URL = getenv("BACKEND_BASE_URL", "http://localhost:8000")


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


async def craft_and_send_email(
    employee: employee_models.Employee,
    arrangements: List[ArrangementResponse],
    action: Action,
    current_approval_status: ApprovalStatus,
    manager: employee_models.Employee,
    auto_reject: Optional[bool] = False,
):
    logger.info("Crafting and sending email notifications...")

    email_list = []

    email_content = craft_email_content(
        employee=employee,
        arrangements=arrangements,
        action=action,
        current_approval_status=current_approval_status,
        manager=manager,
        auto_reject=auto_reject,
    )

    email_list.append(
        (
            employee.email,
            email_content["employee"]["subject"],
            email_content["employee"]["content"],
        )
    )

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

    for email, subject, content in email_list:
        logger.info(
            f"Email sent successfully to {email} with the following content:\n\n{subject}\n{content}\n\n"
        )


def craft_email_content(
    employee: employee_models.Employee,
    arrangements: List[ArrangementResponse],
    action: Action,
    current_approval_status: ApprovalStatus,
    manager: employee_models.Employee,
    auto_reject: bool = False,
):
    formatted_details = format_details(arrangements, action)

    result = {
        "employee": {
            "subject": format_email_subject("employee", action, current_approval_status),
            "content": format_email_body(employee, formatted_details, "employee", auto_reject),
        },
        "manager": {
            "subject": format_email_subject("manager", action, current_approval_status),
            "content": format_email_body(manager, formatted_details, "manager", auto_reject),
        },
    }

    return result


def format_details(arrangements: List[ArrangementResponse], action: Action):
    details = []
    for arrangement in arrangements:
        status_change_reason = ""
        if action != Action.CREATE:
            status_change_reason = f"Reason for Status Change: {arrangement.status_reason}\n"
        details.append(
            (
                f"Request ID: {arrangement.arrangement_id}\n"
                f"WFH Date: {arrangement.wfh_date}\n"
                f"WFH Type: {arrangement.wfh_type.value}\n"
                f"Reason for WFH Request: {arrangement.reason_description}\n"
                f"Batch ID: {arrangement.batch_id}\n"
                f"Request Status: {arrangement.current_approval_status.value}\n"
                f"Updated At: {arrangement.update_datetime}\n"
                f"{status_change_reason}"
            )
        )

    return "\n".join(details)


def format_email_subject(
    role: str, action: Action, current_approval_status: ApprovalStatus, auto_reject: bool = False
):
    statement_dict = {
        "employee": {
            Action.CREATE: "Your WFH Request Has Been Created",
            Action.APPROVE: {
                ApprovalStatus.APPROVED: "Your WFH Request Has Been Approved",
                ApprovalStatus.WITHDRAWN: "Your WFH Request Has Been Withdrawn",
            },
            Action.REJECT: {
                ApprovalStatus.REJECTED: {
                    "auto": "Your WFH Request Has Been Auto-Rejected",
                    "manual": "Your WFH Request Has Been Rejected",
                },
                ApprovalStatus.APPROVED: "Your WFH Request Withdrawal Has Been Rejected",
            },
            Action.WITHDRAW: "You Have Requested to Withdraw Your WFH",
            Action.CANCEL: "Your WFH Request Has Been Cancelled",  # Added entry
        },
        "manager": {
            Action.CREATE: "Your Staff Created a WFH Request",
            Action.APPROVE: {
                ApprovalStatus.APPROVED: "You Have Approved a WFH Request",
                ApprovalStatus.WITHDRAWN: "You Have Approved a WFH Request Withdrawal",
            },
            Action.REJECT: {
                ApprovalStatus.REJECTED: {
                    "auto": "Your Staff's WFH Request Has Been Auto-Rejected",
                    "manual": "You Have Rejected a WFH Request",
                },
                ApprovalStatus.APPROVED: "You Have Rejected a WFH Request Withdrawal",
            },
            Action.WITHDRAW: "Your Staff Has Requested to Withdraw Their WFH",
            Action.CANCEL: "A Staff Member's WFH Request Has Been Cancelled",  # Added entry
        },
    }

    action_statement = statement_dict[role][action]
    if action == Action.APPROVE or action == Action.REJECT:
        action_statement = action_statement[current_approval_status]
        if (
            action == Action.REJECT
            and current_approval_status == ApprovalStatus.REJECTED
            and auto_reject
        ):
            action_statement = action_statement["auto"]

    return f"[All-In-One] {action_statement}"


def format_email_body(
    employee: employee_models.Employee,
    formatted_details: str,
    role: str,
    auto_reject: bool = False,
):
    body = f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
    body += (
        "A WFH request has been automatically rejected as it was submitted less than 24 hours before the requested WFH date.\n\n"
        if auto_reject
        else ""
    )
    body += "Please refer to the following details for the above action:\n\n"
    body += formatted_details
    body += (
        "Please ensure future WFH requests are submitted at least 24 hours in advance.\n\n"
        if auto_reject and role == "employee"
        else ""
    )
    body += "\n\nThis email is auto-generated. Please do not reply to this email. Thank you."
    return body


def craft_email_content_for_delegation(
    employee: employee_models.Employee, counterpart_employee: employee_models.Employee, event: str
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


# ============================ DEPRECATED FUNCTIONS ============================
# async def craft_and_send_auto_rejection_email(
#     arrangement_id: int,
#     db: Session,
# ):
#     """Send auto-rejection email for arrangement submitted <24h before WFH date."""
#     # Get arrangement details
#     arrangement = (
#         db.query(LatestArrangement)
#         .filter(LatestArrangement.arrangement_id == arrangement_id)
#         .first()
#     )

#     if not arrangement:
#         raise ValueError(f"Arrangement {arrangement_id} not found")

#     employee = arrangement.requester_info
#     manager = (
#         arrangement.delegate_approving_officer_info
#         if arrangement.delegate_approving_officer_info
#         else arrangement.approving_officer_info
#     )

#     # Create and send emails
#     employee_subject = "[All-In-One] Your WFH Request Has Been Auto-Rejected"
#     employee_content = (
#         f"Dear {employee.staff_fname} {employee.staff_lname},\n\n"
#         f"Your WFH request has been automatically rejected as it was submitted less than 24 hours "
#         f"before the requested WFH date.\n\n"
#         f"Request Details:\n"
#         f"Request ID: {arrangement.arrangement_id}\n"
#         f"WFH Date: {arrangement.wfh_date}\n"
#         f"Type: {arrangement.wfh_type}\n"
#         f"Reason: {arrangement.reason_description}\n\n"
#         f"Please ensure future WFH requests are submitted at least 24 hours in advance.\n\n"
#         f"This email is auto-generated. Please do not reply to this email. Thank you."
#     )

#     manager_subject = "[All-In-One] Staff WFH Request Auto-Rejected"
#     manager_content = (
#         f"Dear {manager.staff_fname} {manager.staff_lname},\n\n"
#         f"A WFH request from your staff has been automatically rejected as it was submitted less "
#         f"than 24 hours before the requested WFH date.\n\n"
#         f"Request Details:\n"
#         f"Staff: {employee.staff_fname} {employee.staff_lname}\n"
#         f"Request ID: {arrangement.arrangement_id}\n"
#         f"WFH Date: {arrangement.wfh_date}\n"
#         f"Type: {arrangement.wfh_type}\n"
#         f"Reason: {arrangement.reason_description}\n\n"
#         f"This email is auto-generated. Please do not reply to this email. Thank you."
#     )

#     email_errors = []
#     email_list = [
#         (employee.email, employee_subject, employee_content),
#         (manager.email, manager_subject, manager_content),
#     ]

#     for email in email_list:
#         try:
#             await send_email(*email)
#         except HTTPException:
#             email_errors.append(email[0])

#     if email_errors:
#         raise exceptions.EmailNotificationException(email_errors)

#     for email, subject, content in email_list:
#         logger.info(f"Auto-rejection email sent successfully to {email} with subject: {subject}")
