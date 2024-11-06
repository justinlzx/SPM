from datetime import datetime
from os import getenv
from typing import Union

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from ..arrangements.commons.enums import Action
from ..logger import logger
from . import exceptions
from .commons.dataclasses import (
    ArrangementNotificationConfig,
    DelegateNotificationConfig,
)
from .commons.structs import ARRANGEMENT_SUBJECT, DELEGATION_SUBJECT

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
    config: Union[ArrangementNotificationConfig, DelegateNotificationConfig],
):
    logger.info("Crafting and sending email notifications...")

    email_list = []

    email_content = craft_email_content(config)

    role_1, role_2 = (
        ("employee", "manager")
        if isinstance(config, ArrangementNotificationConfig)
        else ("delegator", "delegatee")
    )

    email_list.append(
        (
            getattr(config, role_1).email,
            email_content[role_1]["subject"],
            email_content[role_1]["content"],
        )
    )

    email_list.append(
        (
            getattr(config, role_2).email,
            email_content[role_2]["subject"],
            email_content[role_2]["content"],
        )
    )

    email_errors = []

    for email, subject, content in email_list:
        try:
            await send_email(email, subject, content)
            logger.info(
                f"Email sent successfully to {email} with the following content:\n\n{subject}\n{content}\n\n"
            )
        except HTTPException:
            email_errors.append(email)

    if email_errors:
        raise exceptions.EmailNotificationException(email_errors)


def craft_email_content(
    config: Union[ArrangementNotificationConfig, DelegateNotificationConfig],
):
    formatted_details = format_details(config)

    role_1, role_2 = (
        ("employee", "manager")
        if isinstance(config, ArrangementNotificationConfig)
        else ("delegator", "delegatee")
    )

    result = {
        role_1: {
            "subject": format_email_subject(role_1, config),
            "content": format_email_body(role_1, formatted_details, config),
        },
        role_2: {
            "subject": format_email_subject(role_2, config),
            "content": format_email_body(role_2, formatted_details, config),
        },
    }

    return result


def format_details(config: Union[ArrangementNotificationConfig, DelegateNotificationConfig]):
    details = ""
    if isinstance(config, ArrangementNotificationConfig):
        for arrangement in config.arrangements:
            status_change_reason = (
                f"Reason for Status Change: {arrangement.status_reason}\n"
                if config.action != Action.CREATE
                else ""
            )
            details += f"Request ID: {arrangement.arrangement_id}\n"
            details += f"WFH Date: {arrangement.wfh_date}\n"
            details += f"WFH Type: {arrangement.wfh_type.value}\n"
            details += f"Reason for WFH Request: {arrangement.reason_description}\n"
            details += f"Batch ID: {arrangement.batch_id}\n"
            details += f"Request Status: {arrangement.current_approval_status.value}\n"
            details += f"Updated At: {arrangement.update_datetime}\n"
            details += f"{status_change_reason}\n\n"
    else:
        verb_map = {
            "delegate": "Delegation",
            "undelegate": "Undelegation",
            "approved": "Delegation Approval",
            "rejected": "Delegation Rejection",
            "withdrawn": "Delegation Withdrawal",
        }

        details += f"{verb_map.get(config.action)} Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        details += f"Delegator: {config.delegator.staff_fname} {config.delegator.staff_lname}\n"
        details += f"Delegatee: {config.delegatee.staff_fname} {config.delegatee.staff_lname}\n"

    return details


def format_email_subject(
    role: str, config: Union[ArrangementNotificationConfig, DelegateNotificationConfig]
):
    if isinstance(config, ArrangementNotificationConfig):
        subject = ARRANGEMENT_SUBJECT[role][config.action]

        if config.action == Action.APPROVE or config.action == Action.REJECT:
            subject = subject[config.current_approval_status]
    else:
        subject = DELEGATION_SUBJECT[role][config.action]

    return f"[All-In-One] {subject}"


def format_email_body(
    role: str,
    formatted_details: str,
    config: Union[ArrangementNotificationConfig, DelegateNotificationConfig],
):
    # Add common header
    body = f"Dear {getattr(config, role).staff_fname} {getattr(config, role).staff_lname},\n\n"

    if isinstance(config, ArrangementNotificationConfig):
        body += (
            "A WFH request has been automatically rejected as it was submitted less than 24 hours before the requested WFH date.\n\n"
            if config.auto_reject
            else ""
        )
        body += "Please refer to the following details for the above action:\n\n"
        body += formatted_details
        body += (
            "Please ensure future WFH requests are submitted at least 24 hours in advance.\n\n"
            if config.auto_reject and role == "employee"
            else ""
        )
    else:
        if role == "delegator" and config.action == "delegate":
            body += "You have delegated your approval responsibilities to "
            body += f"{config.delegatee.staff_fname} {config.delegatee.staff_lname}.\n\n"
            body += "This delegation will take effect immediately upon acceptance. Any pending approvals will "
            body += (
                f"be handled by {config.delegatee.staff_fname} once they accept the delegation.\n"
            )

        elif role == "delegatee" and config.action == "delegate":
            body += f"{config.delegator.staff_fname} {config.delegator.staff_lname} has delegated their "
            body += "approval responsibilities to you.\n\n"
            body += "Please log in to the portal to review and accept the delegation.\n"
            body += "Once accepted, any pending approvals assigned to "
            body += f"{config.delegator.staff_fname} will be routed to you.\n\n"

        elif role == "delegator" and config.action == "undelegate":
            body += "The delegation of approval responsibilities between you and "
            body += f"{config.delegatee.staff_fname} {config.delegatee.staff_lname} has been revoked.\n\n"
            body += "All pending approvals will be reassigned to the original manager, and you no longer have the responsibility "
            body += f"for approvals on behalf of {config.delegatee.staff_fname}.\n"

        elif role == "delegatee" and config.action == "undelegate":
            body += "The delegation of approval responsibilities between you and "
            body += f"{config.delegator.staff_fname} {config.delegator.staff_lname} has been revoked.\n\n"
            body += "All pending approvals will be reassigned to the original manager, and you no longer have the responsibility "
            body += "for approvals on behalf of the delegator.\n"

        elif role == "delegator" and config.action == "approved":
            body += "Your delegation request to "
            body += f"{config.delegatee.staff_fname} {config.delegatee.staff_lname} has been approved.\n\n"

        elif role == "delegatee" and config.action == "approved":
            body += f"{config.delegator.staff_fname} {config.delegator.staff_lname} has approved your delegation request.\n\n"

        elif role == "delegator" and config.action == "rejected":
            body += "Your delegation request to "
            body += f"{config.delegatee.staff_fname} {config.delegatee.staff_lname} has been rejected.\n\n"

        elif role == "delegatee" and config.action == "rejected":
            body += f"{config.delegator.staff_fname} {config.delegator.staff_lname} has rejected your delegation request.\n\n"

        elif role == "delegator" and config.action == "withdrawn":
            body += "Your delegation to "
            body += f"{config.delegatee.staff_fname} {config.delegatee.staff_lname} has been withdrawn.\n\n"

        elif role == "delegatee" and config.action == "withdrawn":
            body += f"The delegation assigned to you by {config.delegator.staff_fname} {config.delegator.staff_lname} has been withdrawn.\n\n"

        body += formatted_details

    # Add common footer
    body += "\n\nThis email is auto-generated. Please do not reply to this email. Thank you."

    return body
