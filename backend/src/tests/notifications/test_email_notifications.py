import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from dotenv import load_dotenv
from fastapi import HTTPException
from httpx import RequestError
from src.arrangements.commons.enums import Action, ApprovalStatus, WfhType
from src.notifications import email_notifications as notifications
from src.notifications import exceptions as notification_exceptions
from src.notifications.commons.dataclasses import (
    ArrangementNotificationConfig,
    DelegateNotificationConfig,
)

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# ============================== TEST FIXTURES ============================== #


class MockArrangement(MagicMock):
    def __init__(
        self,
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        reason_description="Personal reason",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.arrangement_id = 1
        self.wfh_date = "2024-10-07"
        self.wfh_type = "full"
        self.reason_description = reason_description
        self.batch_id = 1
        self.current_approval_status = current_approval_status
        self.update_datetime = "2024-10-06T12:34:56"
        # self.status_reason = "Rejected due to insufficient explanation"


@pytest.fixture
def mock_arrangement_factory():
    def _create_mock_arrangement(current_approval_status=ApprovalStatus.PENDING_APPROVAL):
        return MockArrangement(current_approval_status=current_approval_status)

    return _create_mock_arrangement


@pytest.fixture
def mock_arrangement_config_factory():
    def _create_mock_arrangement_config(
        employee, arrangements, action, current_approval_status, manager
    ):
        return ArrangementNotificationConfig(
            employee=employee,
            arrangements=arrangements,
            action=action,
            current_approval_status=current_approval_status,
            manager=manager,
        )

    return _create_mock_arrangement_config


@pytest.fixture
def mock_delegate_config_factory():
    def _create_mock_delegate_config(delegator, delegatee, action):
        return DelegateNotificationConfig(
            delegator=delegator,
            delegatee=delegatee,
            action=action,
        )

    return _create_mock_delegate_config


@pytest.fixture
def mock_staff():
    mock = MagicMock()
    mock.staff_fname = "Jane"
    mock.staff_lname = "Doe"
    mock.email = "jane.doe@allinone.com.sg"
    return mock


@pytest.fixture
def mock_manager():
    mock = MagicMock()
    mock.staff_fname = "Michael"
    mock.staff_lname = "Scott"
    mock.email = "michael.scott@allinone.com.sg"
    return mock


async def send_email(to_email: str, subject: str, content: str):
    if not to_email:
        raise HTTPException(status_code=400, detail="Recipient email must be provided.")
    if not subject:
        raise HTTPException(status_code=400, detail="Subject must be provided.")
    if not content:
        raise HTTPException(status_code=400, detail="Content must be provided.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/email/sendemail",
                data={"to_email": to_email, "subject": subject, "content": content},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while sending the email: {str(e)}"
        )


class TestSendEmail:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_success(self, mock_post: MagicMock):
        # Mock response data
        mock_response_data = {"status": "success"}

        # Simulate the mock to return a successful response
        mock_post.return_value.json = MagicMock(return_value=mock_response_data)
        mock_post.return_value.status_code = 200

        # Call the function
        result = await send_email(
            to_email="test@example.com", subject="Test Subject", content="Test Content"
        )

        # Assertions
        assert result == mock_response_data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/email/sendemail",
            data={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "content": "Test Content",
            },
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_failure(self, mock_post: MagicMock):
        # Set the mock to return an unsuccessful response
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"

        # Call the function and check for HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await send_email(
                to_email="test@example.com", subject="Test Subject", content="Test Content"
            )

        assert exc_info.value.status_code == 500
        assert "Internal Server Error" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_request_error(self, mock_post: MagicMock):
        """Test network failure scenario for send_email."""
        # Simulate a network error
        mock_post.side_effect = RequestError("Network error")

        # Call the function and check for HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await send_email(
                to_email="test@example.com", subject="Test Subject", content="Test Content"
            )

        # Updated assertion to match the correct error message
        assert "An error occurred while sending the email: Network error" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_http_exception(self, mock_post: MagicMock):
        # Simulate a request error when sending the email
        mock_post.side_effect = httpx.RequestError("Request failed")

        # Call the function and check for HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await send_email("to_email@example.com", "Test Subject", "Test Content")

        assert exc_info.value.status_code == 500
        assert "An error occurred while sending the email: Request failed" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_invalid_response(self, mock_post: MagicMock):
        # Mock invalid response
        mock_post.return_value.status_code = 403
        mock_post.return_value.text = "Forbidden"

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")

        assert exc_info.value.status_code == 403
        assert "Forbidden" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_empty_inputs(self):
        with pytest.raises(HTTPException) as exc_info:
            await send_email("", "Test Subject", "Test Content")
        assert exc_info.value.detail == "Recipient email must be provided."

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "", "Test Content")
        assert exc_info.value.detail == "Subject must be provided."

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "")
        assert exc_info.value.detail == "Content must be provided."

    @pytest.mark.asyncio
    @patch("src.notifications.email_notifications.httpx.AsyncClient.post")
    async def test_invalid_email_format(self, mock_post: MagicMock):
        # Simulate the behavior where an invalid email format causes an HTTPException
        mock_post.side_effect = HTTPException(
            status_code=400, detail="Recipient email must be a valid email address."
        )

        # Test with invalid email format
        with pytest.raises(HTTPException) as exc_info:
            await send_email("invalid-email", "Test Subject", "Test Content")

        # Check if the raised exception contains the correct message
        assert exc_info.value.detail == "Recipient email must be a valid email address."

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad Request"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_network_error(self, mock_post):
        mock_post.side_effect = httpx.RequestError("Network error")

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")
        assert exc_info.value.status_code == 500
        assert "An error occurred while sending the email: Network error" in exc_info.value.detail


class TestFormatEmailSubject:
    @pytest.mark.parametrize(
        (
            "role",
            "action",
            "current_approval_status",
            "expected_subject",
        ),
        [
            (
                "employee",
                Action.CREATE,
                ApprovalStatus.PENDING_APPROVAL,
                "[All-In-One] Your WFH Request Has Been Created",
            ),
            (
                "manager",
                Action.CREATE,
                ApprovalStatus.PENDING_APPROVAL,
                "[All-In-One] Your Staff Created a WFH Request",
            ),
            (
                "employee",
                Action.APPROVE,
                ApprovalStatus.APPROVED,
                "[All-In-One] Your WFH Request Has Been Approved",
            ),
            (
                "manager",
                Action.APPROVE,
                ApprovalStatus.APPROVED,
                "[All-In-One] You Have Approved a WFH Request",
            ),
            (
                "employee",
                Action.APPROVE,
                ApprovalStatus.WITHDRAWN,
                "[All-In-One] Your WFH Request Has Been Withdrawn",
            ),
            (
                "manager",
                Action.APPROVE,
                ApprovalStatus.WITHDRAWN,
                "[All-In-One] You Have Approved a WFH Request Withdrawal",
            ),
            (
                "employee",
                Action.REJECT,
                ApprovalStatus.REJECTED,
                "[All-In-One] Your WFH Request Has Been Rejected",
            ),
            (
                "manager",
                Action.REJECT,
                ApprovalStatus.REJECTED,
                "[All-In-One] You Have Rejected a WFH Request",
            ),
            (
                "employee",
                Action.REJECT,
                ApprovalStatus.APPROVED,
                "[All-In-One] Your WFH Request Withdrawal Has Been Rejected",
            ),
            (
                "manager",
                Action.REJECT,
                ApprovalStatus.APPROVED,
                "[All-In-One] You Have Rejected a WFH Request Withdrawal",
            ),
            (
                "employee",
                Action.WITHDRAW,
                ApprovalStatus.PENDING_WITHDRAWAL,
                "[All-In-One] You Have Requested to Withdraw Your WFH",
            ),
            (
                "manager",
                Action.WITHDRAW,
                ApprovalStatus.PENDING_WITHDRAWAL,
                "[All-In-One] Your Staff Has Requested to Withdraw Their WFH",
            ),
        ],
    )
    def test_success_arrangements(
        self,
        role,
        action,
        current_approval_status,
        expected_subject,
        mock_arrangement_config_factory,
    ):
        # Arrange
        config = mock_arrangement_config_factory(
            employee=MagicMock(),
            arrangements=[MagicMock()],
            action=action,
            current_approval_status=current_approval_status,
            manager=MagicMock(),
        )

        # Act
        email_subject = notifications.format_email_subject(
            role=role,
            config=config,
        )

        # Assert
        assert email_subject == expected_subject

    @pytest.mark.parametrize(
        ("role", "action"),
        [
            ("delegator", "delegate"),
            ("delegator", "undelegated"),
            ("delegator", "approved"),
            ("delegator", "rejected"),
            ("delegator", "withdrawn"),
            ("delegatee", "delegate"),
            ("delegatee", "undelegated"),
            ("delegatee", "approved"),
            ("delegatee", "rejected"),
            ("delegatee", "withdrawn"),
        ],
    )
    def test_success_delegation(self, role, action, mock_delegate_config_factory):
        # Arrange
        config = mock_delegate_config_factory(
            delegator=MagicMock(), delegatee=MagicMock(), action=action
        )

        # Act
        email_subject = notifications.format_email_subject(role=role, config=config)

        # Assert
        assert email_subject is not None


class TestFormatEmailBody:
    @pytest.mark.parametrize(
        "role",
        ["employee", "manager"],
    )
    def test_success_arrangements(self, role, mock_arrangement_config_factory):
        mock_employee = MagicMock()
        mock_employee.configure_mock(
            staff_fname="Jane",
            staff_lname="Doe",
        )

        mock_manager = MagicMock()
        mock_manager.configure_mock(
            staff_fname="Michael",
            staff_lname="Scott",
        )

        mock_formatted_details = ""
        mock_config = mock_arrangement_config_factory(
            employee=mock_employee,
            arrangements=[MagicMock()],
            action=Action.CREATE,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            manager=mock_manager,
        )

        result = notifications.format_email_body(
            role, formatted_details=mock_formatted_details, config=mock_config
        )

        if role == "employee":
            assert f"Dear {mock_employee.staff_fname} {mock_employee.staff_lname}," in result
        else:
            assert f"Dear {mock_manager.staff_fname} {mock_manager.staff_lname}," in result

        assert (
            "\n\nThis email is auto-generated. Please do not reply to this email. Thank you."
            in result
        )

    @pytest.mark.parametrize(
        ("role", "action"),
        [
            ("delegator", "delegate"),
            ("delegator", "undelegated"),
            ("delegator", "approved"),
            ("delegator", "rejected"),
            ("delegator", "withdrawn"),
            ("delegatee", "delegate"),
            ("delegatee", "undelegated"),
            ("delegatee", "approved"),
            ("delegatee", "rejected"),
            ("delegatee", "withdrawn"),
        ],
    )
    def test_success_delegate(self, role, action, mock_delegate_config_factory):
        # Arrange
        mock_delegator = MagicMock()
        mock_delegator.configure_mock(
            staff_fname="Jane",
            staff_lname="Doe",
        )

        mock_delegatee = MagicMock()
        mock_delegatee.configure_mock(
            staff_fname="Michael",
            staff_lname="Scott",
        )

        mock_formatted_details = ""
        mock_config = mock_delegate_config_factory(
            delegator=mock_delegator, delegatee=mock_delegatee, action=action
        )

        # Act
        result = notifications.format_email_body(
            role=role, formatted_details=mock_formatted_details, config=mock_config
        )

        # Assert
        if role == "delegator":
            assert f"Dear {mock_delegator.staff_fname} {mock_delegator.staff_lname}," in result
        else:
            assert f"Dear {mock_delegatee.staff_fname} {mock_delegatee.staff_lname}," in result


class TestFormatDetails:
    @pytest.mark.parametrize(
        "action",
        [Action.CREATE, Action.APPROVE],
    )
    def test_success_arrangements(self, action, mock_arrangement_config_factory):
        arrangement_id = 1
        wfh_date = "2024-10-07"
        wfh_type = WfhType.FULL
        reason_description = "Personal reason"
        batch_id = 1
        current_approval_status = ApprovalStatus.PENDING_APPROVAL
        update_datetime = "2024-10-06T12:34:56"
        status_reason = "Rejected due to insufficient explanation"

        mock_arrangement = MagicMock()
        mock_arrangement.configure_mock(
            arrangement_id=arrangement_id,
            wfh_date=wfh_date,
            wfh_type=wfh_type,
            reason_description=reason_description,
            batch_id=batch_id,
            current_approval_status=current_approval_status,
            update_datetime=update_datetime,
            status_reason=status_reason,
        )

        mock_config = mock_arrangement_config_factory(
            employee=MagicMock(),
            arrangements=[mock_arrangement],
            action=action,
            current_approval_status=current_approval_status,
            manager=MagicMock(),
        )

        result = notifications.format_details(mock_config)

        assert f"Request ID: {arrangement_id}" in result
        assert f"WFH Date: {wfh_date}" in result
        assert f"WFH Type: {wfh_type.value}" in result
        assert f"Reason for WFH Request: {reason_description}" in result
        assert f"Batch ID: {batch_id}" in result
        assert f"Request Status: {current_approval_status.value}" in result
        assert f"Updated At: {update_datetime}" in result

        if action != Action.CREATE:
            assert f"Reason for Status Change: {status_reason}" in result

    @pytest.mark.parametrize(
        "action",
        [
            "delegate",
            "undelegated",
            "approved",
            "rejected",
            "withdrawn",
        ],
    )
    def test_success_delegate(self, action, mock_delegate_config_factory):
        # Arrange
        mock_delegator = MagicMock()
        mock_delegator.configure_mock(
            staff_fname="Jane",
            staff_lname="Doe",
        )

        mock_delegatee = MagicMock()
        mock_delegatee.configure_mock(
            staff_fname="Michael",
            staff_lname="Scott",
        )

        mock_config = mock_delegate_config_factory(
            delegator=mock_delegator, delegatee=mock_delegatee, action=action
        )

        # Act
        result = notifications.format_details(mock_config)

        # Assert
        assert "Date: " in result
        assert f"Delegator: {mock_delegator.staff_fname} {mock_delegator.staff_lname}" in result
        assert f"Delegatee: {mock_delegatee.staff_fname} {mock_delegatee.staff_lname}" in result


@patch("src.notifications.email_notifications.format_email_body")
@patch("src.notifications.email_notifications.format_email_subject")
@patch("src.notifications.email_notifications.format_details")
class TestCraftEmailContent:

    def test_success_arrangements(
        self, mock_details, mock_subject, mock_body, mock_arrangement_config_factory
    ):
        # Arrange
        mock_config = mock_arrangement_config_factory(
            employee=MagicMock(),
            arrangements=[MagicMock()],
            action=Action.CREATE,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            manager=MagicMock(),
        )

        # Act
        result = notifications.craft_email_content(mock_config)

        # Assert
        mock_details.assert_called_once()
        mock_subject.assert_called()
        assert mock_subject.call_count == 2
        mock_body.assert_called()
        assert mock_body.call_count == 2

        assert result == {
            "employee": {
                "subject": mock_subject.return_value,
                "content": mock_body.return_value,
            },
            "manager": {
                "subject": mock_subject.return_value,
                "content": mock_body.return_value,
            },
        }

    def test_success_delegate(
        self, mock_details, mock_subject, mock_body, mock_delegate_config_factory
    ):
        # Arrange
        mock_config = mock_delegate_config_factory(
            delegator=MagicMock(),
            delegatee=MagicMock(),
            action="delegate",
        )

        # Act
        result = notifications.craft_email_content(mock_config)

        # Assert
        mock_details.assert_called_once()
        mock_subject.assert_called()
        assert mock_subject.call_count == 2
        mock_body.assert_called()
        assert mock_body.call_count == 2

        assert result == {
            "delegator": {
                "subject": mock_subject.return_value,
                "content": mock_body.return_value,
            },
            "delegatee": {
                "subject": mock_subject.return_value,
                "content": mock_body.return_value,
            },
        }


@patch("src.notifications.email_notifications.send_email")
@patch(
    "src.notifications.email_notifications.craft_email_content",
    return_value={
        "employee": {"subject": "Test Subject", "content": "Test Content"},
        "manager": {"subject": "Test Subject", "content": "Test Content"},
    },
)
class TestCraftAndSendEmail:
    @pytest.mark.asyncio
    async def test_success(
        self,
        mock_craft_email,
        mock_send_email,
        mock_arrangement_config_factory,
    ):
        """Test crafting and sending email for different actions."""
        # Arrange
        mock_employee = MagicMock()
        mock_employee.email = "jane.doe@allinone.com.sg"

        mock_manager = MagicMock()
        mock_manager.email = "michael.scott@allinone.com.sg"

        mock_config = mock_arrangement_config_factory(
            employee=mock_employee,
            arrangements=[MagicMock()],
            action=Action.CREATE,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            manager=mock_manager,
        )

        # Act
        await notifications.craft_and_send_email(mock_config)

        # Assert
        mock_craft_email.assert_called_once()
        mock_send_email.assert_called()
        assert mock_send_email.call_count == 2

    @pytest.mark.asyncio
    async def test_email_failure(
        self, mock_craft_email, mock_send_email, mock_arrangement_config_factory
    ):
        # Arrange
        mock_employee = MagicMock()
        mock_employee.email = "jane.doe@allinone.com.sg"

        mock_manager = MagicMock()
        mock_manager.email = "michael.scott@allinone.com.sg"

        mock_config = mock_arrangement_config_factory(
            employee=mock_employee,
            arrangements=[MagicMock()],
            action=Action.CREATE,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            manager=mock_manager,
        )

        mock_send_email.side_effect = HTTPException(status_code=500, detail="Internal Server Error")

        # Act and Assert
        with pytest.raises(notification_exceptions.EmailNotificationException) as exc_info:
            await notifications.craft_and_send_email(mock_config)
        assert (
            str(exc_info.value)
            == "Failed to send emails to jane.doe@allinone.com.sg, michael.scott@allinone.com.sg"
        )
