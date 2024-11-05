import os
from unittest.mock import AsyncMock, MagicMock, patch

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
    async def test_successful_send(self):
        """Test successful email sending with context manager"""
        # Setup response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Email sent", "id": "123"}

        # Setup client mock
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        # Setup context manager mock
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_async_client):
            result = await send_email("test@example.com", "Test Subject", "Test Content")

        assert result == {"message": "Email sent", "id": "123"}
        mock_client.post.assert_called_once_with(
            f"{BASE_URL}/email/sendemail",
            data={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "content": "Test Content",
            },
        )

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test validation of input parameters"""
        # Test empty email
        with pytest.raises(HTTPException) as exc:
            await send_email("", "subject", "content")
        assert exc.value.detail == "Recipient email must be provided."

        # Test empty subject
        with pytest.raises(HTTPException) as exc:
            await send_email("test@email.com", "", "content")
        assert exc.value.detail == "Subject must be provided."

        # Test empty content
        with pytest.raises(HTTPException) as exc:
            await send_email("test@email.com", "subject", "")
        assert exc.value.detail == "Content must be provided."

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_with_valid_json_response(self, mock_client):
        # Setup mock response with specific JSON data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message_id": "123", "status": "sent"}

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Call function
        result = await send_email("test@example.com", "Test Subject", "Test Content")

        # Verify the full JSON response is returned
        assert result == {"message_id": "123", "status": "sent"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_request_error_handling(self, mock_client):
        # Setup mock client to raise RequestError
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Call function and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")

        assert exc_info.value.status_code == 500
        assert "Connection failed" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_email_send(self, mock_client):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Call function
        result = await send_email("test@example.com", "Test Subject", "Test Content")

        # Verify the result and calls
        assert result == {"status": "success"}
        mock_client_instance.post.assert_called_once_with(
            f"{BASE_URL}/email/sendemail",
            data={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "content": "Test Content",
            },
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_failed_email_send_non_200(self, mock_client):
        # Setup mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Call function and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad Request"

    @pytest.mark.asyncio
    async def test_non_200_response(self):
        """Test handling of non-200 response"""
        # Setup response mock
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid email format"

        # Setup client mock
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        # Setup context manager mock
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_async_client):
            with pytest.raises(HTTPException) as exc:
                await send_email("test@example.com", "Test Subject", "Test Content")

        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid email format"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_happy_path(self, mock_post):
        """Test successful email sending"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "success"}
        mock_post.return_value = mock_response

        result = await send_email("test@example.com", "Test Subject", "Test Content")

        assert result == {"message": "success"}
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
    async def test_email_send_retry_logic(self, mock_post):
        """Test email sending with initial failure and retry"""
        # First call fails, second succeeds
        mock_post.side_effect = [
            RequestError("Connection failed"),
            MagicMock(status_code=200, json=lambda: {"message": "Success"}),
        ]

        with pytest.raises(HTTPException) as exc_info:
            await send_email("test@example.com", "Test Subject", "Test Content")

        assert "Connection failed" in str(exc_info.value.detail)
        assert mock_post.call_count == 1

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_multiple_consecutive_sends(self, mock_post):
        """Test multiple consecutive email sends"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Email sent successfully"}
        mock_post.return_value = mock_response

        # Send multiple emails
        for i in range(3):
            result = await send_email(
                f"test{i}@example.com", f"Test Subject {i}", f"Test Content {i}"
            )
            assert result == {"message": "Email sent successfully"}

        assert mock_post.call_count == 3

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_long_email_content(self, mock_post):
        """Test email sending with long content"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Email sent successfully"}
        mock_post.return_value = mock_response

        # Create a long content string
        long_content = "Test content\n" * 1000

        result = await send_email("test@example.com", "Test Subject", long_content)

        assert result == {"message": "Email sent successfully"}
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_email_send_with_special_characters(self, mock_post):
        """Test email sending with special characters in content"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Email sent successfully"}
        mock_post.return_value = mock_response

        # Test with special characters
        result = await send_email(
            "test@example.com",
            "Test Subject with 特殊字符",
            "Content with special characters: ñ, é, 漢字",
        )

        assert result == {"message": "Email sent successfully"}
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_basic_email_send(self, mock_post):
        """Test successful email sending with mock response"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Email sent successfully"}
        mock_post.return_value = mock_response

        # Test the function
        result = await send_email("test@example.com", "Test Subject", "Test Content")

        # Verify the result
        assert result == {"message": "Email sent successfully"}
        mock_post.assert_called_once()

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
    async def test_response_json_parsing(self):
        """Test successful JSON response parsing"""
        # Setup response mock with specific JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123", "status": "delivered"}

        # Setup client mock
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        # Setup context manager mock
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_async_client):
            result = await send_email("test@example.com", "Test Subject", "Test Content")

        assert result == {"id": "msg_123", "status": "delivered"}
        assert mock_response.json.called

    @pytest.mark.asyncio
    async def test_request_error(self):
        """Test handling of request errors"""
        # Setup client mock with error
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.RequestError("Connection timeout")

        # Setup context manager mock
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_async_client):
            with pytest.raises(HTTPException) as exc:
                await send_email("test@example.com", "Test Subject", "Test Content")

        assert exc.value.status_code == 500
        assert "Connection timeout" in exc.value.detail

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
    @pytest.mark.asyncio
    async def test_delegatee_action_withdrawn(self, mock_delegate_config_factory):
        """Test the delegatee-withdrawn branch specifically"""
        # Create mock delegator and delegatee
        mock_delegator = MagicMock()
        mock_delegator.staff_fname = "John"
        mock_delegator.staff_lname = "Doe"

        mock_delegatee = MagicMock()
        mock_delegatee.staff_fname = "Jane"
        mock_delegatee.staff_lname = "Smith"

        # Create config with action="withdrawn"
        config = mock_delegate_config_factory(
            delegator=mock_delegator, delegatee=mock_delegatee, action="withdrawn"
        )

        # Test with role="delegatee"
        formatted_details = "Test Details"
        result = notifications.format_email_body(
            role="delegatee", formatted_details=formatted_details, config=config
        )

        # Verify expected content
        expected_text = f"The delegation assigned to you by {mock_delegator.staff_fname} {mock_delegator.staff_lname} has been withdrawn"
        assert expected_text in result
        assert formatted_details in result
        assert "This email is auto-generated" in result

    @pytest.mark.asyncio
    async def test_delegatee_other_action(self, mock_delegate_config_factory):
        """Test a different action to ensure branch coverage"""
        mock_delegator = MagicMock()
        mock_delegator.staff_fname = "John"
        mock_delegator.staff_lname = "Doe"

        mock_delegatee = MagicMock()
        mock_delegatee.staff_fname = "Jane"
        mock_delegatee.staff_lname = "Smith"

        config = mock_delegate_config_factory(
            delegator=mock_delegator,
            delegatee=mock_delegatee,
            action="some_other_action",  # Different action to hit the else branch
        )

        formatted_details = "Test Details"
        result = notifications.format_email_body(
            role="delegatee", formatted_details=formatted_details, config=config
        )

        assert formatted_details in result
        assert "This email is auto-generated" in result

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
