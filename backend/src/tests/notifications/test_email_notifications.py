import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from dotenv import load_dotenv
from fastapi import HTTPException
from httpx import RequestError
from src.notifications import email_notifications as notifications
from src.notifications import exceptions as notification_exceptions

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# ============================== TEST FIXTURES ============================== #


class MockArrangement(MagicMock):
    def __init__(self, current_approval_status="", reason_description="Personal reason", **kwargs):
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
def mock_create_arrangement():
    return MockArrangement(current_approval_status="pending")


@pytest.fixture
def mock_approve_arrangement():
    return MockArrangement(current_approval_status="approved")


@pytest.fixture
def mock_reject_arrangement():
    return MockArrangement(current_approval_status="rejected")


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


class TestFetchManagerInfo:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_success(self, mock_get: MagicMock):
        # Mock response data
        mock_response_data = {"manager_id": 1, "manager_name": "John Doe"}

        # Simulate the mock to return a successful response
        mock_get.return_value.json = MagicMock(return_value=mock_response_data)
        mock_get.return_value.status_code = 200

        # Call the function
        result = await notifications.fetch_manager_info(staff_id=123)

        # Assertions
        assert result == mock_response_data
        mock_get.assert_called_once_with(f"{BASE_URL}/employees/manager/peermanager/123")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_failure(self, mock_get: MagicMock):
        # Set the mock to return an unsuccessful response
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = "Not Found"

        # Call the function and check for HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await notifications.fetch_manager_info(staff_id=123)

        assert exc_info.value.status_code == 404
        assert "Error fetching manager info" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_request_error(self, mock_get: MagicMock):
        """Test network failure scenario for fetch_manager_info."""
        # Simulate a network error
        mock_get.side_effect = RequestError("Network error")

        # Call the function and check for HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await notifications.fetch_manager_info(staff_id=123)

        # Updated assertion to match the correct error message
        assert "An error occurred while fetching manager info" in exc_info.value.detail


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


class TestCraftEmailContent:
    def test_error_message(self, mock_staff, mock_manager, mock_create_arrangement):
        error_message = "Some error occurred"

        email_subject_content = notifications.craft_email_content(
            employee=mock_staff,
            arrangements=[mock_create_arrangement],
            action="create",
            error_message=error_message,
            manager=mock_manager,
        )
        employee = email_subject_content["employee"]

        assert "[All-In-One] Unsuccessful Creation of WFH Request" in employee["subject"]
        assert (
            "Unfortunately, there was an error processing your WFH request" in employee["content"]
        )
        assert error_message in employee["content"]

    def test_empty_description(self, mock_staff, mock_manager, mock_create_arrangement):
        mock_create_arrangement.reason_description = ""
        email_subject_content = notifications.craft_email_content(
            employee=mock_staff,
            arrangements=[mock_create_arrangement],
            action="create",
            manager=mock_manager,
        )
        employee = email_subject_content["employee"]

        assert "Reason for WFH Request: \n" in employee["content"]

    def test_formatted_details(self, mock_staff, mock_manager, mock_create_arrangement):
        email_subject_content = notifications.craft_email_content(
            employee=mock_staff,
            arrangements=[mock_create_arrangement],
            action="create",
            manager=mock_manager,
        )
        employee = email_subject_content["employee"]

        assert "Request ID: 1" in employee["content"]
        assert "WFH Date: 2024-10-07" in employee["content"]
        assert "Type: full" in employee["content"]
        assert "Reason for WFH Request: Personal reason" in employee["content"]
        assert "Batch ID: 1" in employee["content"]
        assert "Request Status: pending" in employee["content"]
        assert "Updated At: 2024-10-06T12:34:56" in employee["content"]

    @pytest.mark.parametrize(
        "action, expected_employee_subject, expected_manager_subject",
        [
            (
                "create",
                "[All-In-One] Successful Creation of WFH Request",
                "[All-In-One] Your Staff Created a WFH Request",
            ),
            (
                "approve",
                "[All-In-One] Your WFH Request Has Been Approved",
                "[All-In-One] You Have Approved a WFH Request",
            ),
            (
                "reject",
                "[All-In-One] Your WFH Request Has Been Rejected",
                "[All-In-One] You Have Rejected a WFH Request",
            ),
            (
                "withdraw",
                "[All-In-One] You Have Requested to Withdraw Your WFH",
                "[All-In-One] Your Staff Has Requested to Withdraw Their WFH",
            ),
            (
                "allow withdraw",
                "[All-In-One] Your WFH Request Has Been Withdrawn",
                "[All-In-One] You Have Approved a WFH Request Withdrawal",
            ),
            (
                "reject withdraw",
                "[All-In-One] Your WFH Request Withdrawal Has Been Rejected",
                "[All-In-One] You Have Rejected a WFH Request Withdrawal",
            ),
            (
                "cancel",
                "[All-In-One] Your WFH Request Has Been Cancelled",
                "[All-In-One] You Have Cancelled a WFH Request",
            ),
        ],
    )
    def test_success_messages_single_arrangement(
        self,
        mock_staff,
        mock_manager,
        mock_create_arrangement,
        action,
        expected_employee_subject,
        expected_manager_subject,
    ):
        email_subject_content = notifications.craft_email_content(
            employee=mock_staff,
            arrangements=[mock_create_arrangement],
            action=action,
            manager=mock_manager,
        )
        employee = email_subject_content["employee"]
        manager = email_subject_content["manager"]

        # Assertions for employee content
        assert expected_employee_subject in employee["subject"]
        assert "Dear Jane Doe" in employee["content"]

        # Assertions for manager content
        assert expected_manager_subject == manager["subject"]
        assert "Dear Michael Scott" in manager["content"]

    def test_multiple_arrangements(self, mock_staff, mock_manager, mock_create_arrangement):
        arrangements = [mock_create_arrangement] * 2
        email_subject_content = notifications.craft_email_content(
            employee=mock_staff, arrangements=arrangements, action="create", manager=mock_manager
        )
        employee = email_subject_content["employee"]
        manager = email_subject_content["manager"]

        assert "Request ID: 1" in employee["content"]
        assert "Request ID: 1" in manager["content"]

        assert "Request ID: 1" in employee["content"]
        assert "Request ID: 1" in manager["content"]


class TestCraftAndSendEmail:
    @pytest.mark.asyncio
    async def test_missing_required_positional_arguments(self, mock_staff, mock_create_arrangement):
        required_args = [
            (
                (None, None, None),
                "craft_email_content() missing 3 required positional argument(s): employee, arrangements, action",
            ),
            (
                (None, [mock_create_arrangement], "create"),
                "craft_email_content() missing 1 required positional argument(s): employee",
            ),
            (
                (mock_staff, None, "create"),
                "craft_email_content() missing 1 required positional argument(s): arrangements",
            ),
            (
                (mock_staff, [], "create"),
                "craft_email_content() missing 1 required positional argument(s): arrangements",
            ),
            (
                (mock_staff, [mock_create_arrangement], None),
                "craft_email_content() missing 1 required positional argument(s): action",
            ),
        ]

        for args, error_msg in required_args:
            with pytest.raises(TypeError) as exc_info:
                await notifications.craft_and_send_email(*args)
            assert str(exc_info.value) == error_msg

    # REVIEW: may not be needed as required employee attributes should be validated by the Pydantic model
    @pytest.mark.asyncio
    async def test_missing_employee_attributes(
        self, mock_staff, mock_manager, mock_create_arrangement
    ):
        mock_staff.staff_fname = None
        with pytest.raises(AttributeError) as exc_info:
            await notifications.craft_and_send_email(
                employee=mock_staff,
                arrangements=[mock_create_arrangement],
                action="create",
                manager=mock_manager,
            )
        assert "Employee is missing required attributes: staff_fname" in str(exc_info.value)

        mock_staff.staff_lname = None
        mock_staff.email = None

        with pytest.raises(AttributeError) as exc_info:
            await notifications.craft_and_send_email(
                employee=mock_staff,
                arrangements=[mock_create_arrangement],
                action="create",
                manager=mock_manager,
            )
        assert "Employee is missing required attributes: staff_fname, staff_lname, email" in str(
            exc_info.value
        )

    # REVIEW: may not be needed as required employee attributes should be validated by the Pydantic model
    # TODO: Test missing manager attributes
    # TODO: Test missing arrangement attributes

    @pytest.mark.asyncio
    @pytest.mark.parametrize("action", ["create", "approve", "reject"])
    async def test_missing_manager(self, mock_staff, mock_create_arrangement, action):
        """Test crafting email content with missing manager for different actions."""
        with pytest.raises(ValueError) as exc_info:
            await notifications.craft_and_send_email(
                employee=mock_staff, arrangements=[mock_create_arrangement], action=action
            )
        assert str(exc_info.value) == "Manager is required for the specified action."

    @pytest.mark.asyncio
    async def test_invalid_action(self, mock_staff, mock_create_arrangement, mock_manager):
        with pytest.raises(ValueError) as excinfo:
            await notifications.craft_and_send_email(
                employee=mock_staff,
                arrangements=[mock_create_arrangement],
                action="invalid_action",
                manager=mock_manager,
            )
        assert str(excinfo.value) == "Invalid action: invalid_action"

    @pytest.mark.asyncio
    async def test_empty_error_message(self, mock_staff, mock_manager, mock_create_arrangement):
        """Test crafting email content for failure scenario with an empty error message."""
        with pytest.raises(ValueError) as exc_info:
            await notifications.craft_and_send_email(
                employee=mock_staff,
                arrangements=[mock_create_arrangement],
                action="create",
                error_message="",
                manager=mock_manager,
            )
        assert str(exc_info.value) == "Error message cannot be an empty string."

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "action, mock_arrangement_fixture",
        [
            ("create", "mock_create_arrangement"),
            ("approve", "mock_approve_arrangement"),
            ("reject", "mock_reject_arrangement"),
        ],
    )
    @patch("src.notifications.email_notifications.send_email", return_value=True)
    async def test_success(
        self, mock_send_email, mock_staff, mock_manager, request, action, mock_arrangement_fixture
    ):
        """Test crafting and sending email for different actions."""
        # Get the appropriate mock arrangement fixture
        mock_arrangement = request.getfixturevalue(mock_arrangement_fixture)

        result = await notifications.craft_and_send_email(
            employee=mock_staff,
            arrangements=mock_arrangement,
            action=action,
            manager=mock_manager,
        )
        assert result is True
        assert mock_send_email.call_count == 2
        mock_send_email.assert_called()

    @pytest.mark.asyncio
    @patch(
        "src.notifications.email_notifications.send_email",
        side_effect=HTTPException(status_code=500),
    )
    async def test_email_failure(
        self, mock_send_email, mock_staff, mock_create_arrangement, mock_manager
    ):

        with pytest.raises(notification_exceptions.EmailNotificationException) as exc_info:
            await notifications.craft_and_send_email(
                employee=mock_staff,
                arrangements=mock_create_arrangement,
                action="create",
                manager=mock_manager,
            )
        assert (
            str(exc_info.value)
            == "Failed to send emails to jane.doe@allinone.com.sg, michael.scott@allinone.com.sg"
        )
        assert mock_send_email.call_count == 2
        mock_send_email.assert_called()

    @pytest.mark.asyncio
    @patch("src.notifications.email_notifications.send_email", return_value=True)
    async def test_create_multiple_arrangements_success(
        self, mock_send_email, mock_staff, mock_manager, mock_create_arrangement
    ):
        mock_arrangements = [mock_create_arrangement] * 2

        result = await notifications.craft_and_send_email(
            employee=mock_staff,
            arrangements=mock_arrangements,
            action="create",
            manager=mock_manager,
        )
        assert result is True
        mock_send_email.assert_called()
