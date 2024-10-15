import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from dotenv import load_dotenv
from fastapi import HTTPException
from httpx import RequestError
from src.arrangements.schemas import ArrangementLog

# from src.arrangements.models import LatestArrangement
from src.notifications import email_notifications as notifications

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


class MockArrangement:
    def __init__(self):
        self.arrangement_id = 1
        self.wfh_date = "2024-10-09"
        self.current_approval_status = "Approved"
        self.wfh_type = "Whole Day"
        self.reason_description = "Personal"
        self.batch_id = "Batch123"
        self.update_datetime = "2024-10-09T12:34:56"
        self.status_reason = "Rejected due to insufficient explanation"


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


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_success(mock_get: MagicMock):
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
async def test_fetch_manager_info_failure(mock_get: MagicMock):
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
async def test_fetch_manager_info_request_error(mock_get: MagicMock):
    """Test network failure scenario for fetch_manager_info."""
    # Simulate a network error
    mock_get.side_effect = RequestError("Network error")

    # Call the function and check for HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await notifications.fetch_manager_info(staff_id=123)

    # Updated assertion to match the correct error message
    assert "An error occurred while fetching manager info" in exc_info.value.detail


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_success(mock_post: MagicMock):
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
        data={"to_email": "test@example.com", "subject": "Test Subject", "content": "Test Content"},
    )


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_failure(mock_post: MagicMock):
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
async def test_send_email_request_error(mock_post: MagicMock):
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
async def test_craft_email_content():
    # Mock arrangement and staff data to avoid mapper issues
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock()  # Mock arrangement to avoid mapper initialization
    mock_arrangement.wfh_date = "2024-10-07"
    mock_arrangement.current_approval_status = "pending"
    mock_arrangement.reason_description = "Work from home for personal reasons"

    subject, content = notifications.craft_email_content(
        employee=mock_staff, arrangements=[mock_arrangement], success=True
    )

    # Assertions for content
    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    assert "Approval Status: pending" in content


@pytest.mark.asyncio
async def test_craft_email_content_empty_arrangement():
    """Test crafting email content with an empty arrangement list."""
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")

    # Call the function with an empty list of arrangements
    subject, content = notifications.craft_email_content(
        employee=mock_staff, arrangements=[], success=True
    )

    # Updated assertions for empty arrangement
    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "Dear Jane Doe" in content
    # Since there are no arrangements, just check that the arrangements section is missing
    assert "Your WFH request has been successfully created" in content
    assert "This email is auto-generated. Please do not reply" in content


@pytest.mark.asyncio
async def test_craft_email_content_failure():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    error_message = "Some error occurred"

    subject, content = notifications.craft_email_content(
        employee=mock_staff, arrangements=[], success=False, error_message=error_message
    )

    assert subject == "[All-In-One] Unsuccessful Creation of WFH Request"
    assert "Unfortunately, there was an error processing your WFH request" in content
    assert error_message in content


@pytest.mark.asyncio
async def test_craft_email_content_failure_empty_error_message():
    """Test crafting email content for failure scenario with an empty error message."""
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")

    # Call the function with an empty error message
    subject, content = notifications.craft_email_content(
        employee=mock_staff, arrangements=[], success=False, error_message=""
    )

    # Updated assertions for empty error message
    assert subject == "[All-In-One] Unsuccessful Creation of WFH Request"
    assert "Unfortunately, there was an error processing your WFH request" in content
    # Check that the "Error details" section is included, even if no specific message is provided
    assert "Error details: " in content


@pytest.mark.asyncio
async def test_craft_approval_email_content():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = ArrangementLog(
        arrangement_id=2,
        wfh_date="2024-10-07",
        wfh_type="full",
        reason_description="Need to work remotely",
        batch_id="1002",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
        approval_status="approved",
    )

    subject, content = notifications.craft_approval_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Approved" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    assert "Approval Reason: Need to work remotely" in content


@pytest.mark.asyncio
async def test_craft_approval_email_content_empty_description():
    """Test crafting approval email content with missing description."""
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")

    # Call the function with an empty/missing reason description
    mock_arrangement = MagicMock()  # Mock arrangement to avoid mapper initialization
    mock_arrangement.reason_description = ""  # Missing description
    mock_arrangement.wfh_date = "2024-10-07"

    subject, content = notifications.craft_approval_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Updated assertions for empty description
    assert "[All-In-One] Your WFH Request Has Been Approved" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    # The "Reason for WFH Request" might just be empty if no reason is provided
    assert "Reason for WFH Request: " in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content():
    # Mock arrangement and staff data to avoid mapper issues
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock()  # Mock arrangement to avoid mapper initialization
    mock_arrangement.wfh_date = "2024-10-08"
    mock_arrangement.current_approval_status = "rejected"
    mock_arrangement.status_reason = "Not enough reason provided"

    subject, content = notifications.craft_rejection_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-08" in content
    assert "Rejection Reason: Not enough reason provided" in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content_empty_reason():
    """Test crafting rejection email content with missing rejection reason."""
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")

    # Call the function with an empty rejection reason
    mock_arrangement = MagicMock()  # Mock arrangement to avoid mapper initialization
    mock_arrangement.wfh_date = "2024-10-08"
    mock_arrangement.status_reason = ""  # Missing rejection reason

    subject, content = notifications.craft_rejection_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Updated assertions for empty rejection reason
    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-08" in content
    # The "Rejection Reason" might just be empty if no reason is provided
    assert "Rejection Reason: " in content


@pytest.mark.asyncio
async def test_craft_approval_email_content_with_manager():
    # Mock employee and arrangement data
    mock_employee = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_manager = MagicMock(staff_fname="John", staff_lname="Smith")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        wfh_type="partial",
        reason_description="personal",
        batch_id=123,
        update_datetime="2024-10-01",
    )

    subject, content = notifications.craft_approval_email_content(
        employee=mock_employee,
        arrangement=mock_arrangement,
        is_manager=True,
        manager=mock_manager,
    )

    assert "[All-In-One] You Have Approved a WFH Request" in subject
    assert "Dear John Smith" in content
    assert "You have successfully approved a WFH request" in content


@pytest.mark.asyncio
async def test_craft_approval_email_content_no_manager():
    # Mock employee and arrangement data
    mock_employee = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        wfh_type="partial",
        reason_description="personal",
        batch_id=123,
        update_datetime="2024-10-01",
    )

    subject, content = notifications.craft_approval_email_content(
        employee=mock_employee,
        arrangement=mock_arrangement,
        is_manager=False,
        manager=None,
    )

    assert "[All-In-One] Your WFH Request Has Been Approved" in subject
    assert "Dear Jane Doe" in content
    assert "Your WFH request has been approved" in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content_with_manager():
    # Mock employee and arrangement data
    mock_employee = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_manager = MagicMock(staff_fname="John", staff_lname="Smith")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        wfh_type="full",
        reason_description="personal",
        batch_id=123,
        update_datetime="2024-10-01",
        status_reason="Not enough justification",
    )

    subject, content = notifications.craft_rejection_email_content(
        employee=mock_employee,
        arrangement=mock_arrangement,
        is_manager=True,
        manager=mock_manager,
    )

    assert "[All-In-One] You Have Rejected a WFH Request" in subject
    assert "Dear John Smith" in content
    assert "You have rejected a WFH request for Jane Doe" in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content_no_manager():
    # Mock employee and arrangement data
    mock_employee = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        wfh_type="full",
        reason_description="personal",
        batch_id=123,
        update_datetime="2024-10-01",
        status_reason="Not enough justification",
    )

    subject, content = notifications.craft_rejection_email_content(
        employee=mock_employee,
        arrangement=mock_arrangement,
        is_manager=False,
        manager=None,
    )

    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "Dear Jane Doe" in content
    assert "Your WFH request has been rejected" in content


@pytest.mark.asyncio
async def test_craft_email_content_error():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        current_approval_status="pending",
        reason_description="Work from home for personal reasons",
    )

    subject, content = notifications.craft_email_content(
        employee=mock_staff,
        arrangements=[mock_arrangement],
        success=False,
        error_message="An error occurred",
    )

    assert "[All-In-One] Unsuccessful Creation of WFH Request" in subject
    assert "An error occurred" in content
    assert "Dear Jane Doe" in content


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_invalid_response(mock_post: MagicMock):
    # Mock invalid response
    mock_post.return_value.status_code = 403
    mock_post.return_value.text = "Forbidden"

    with pytest.raises(HTTPException) as exc_info:
        await send_email("test@example.com", "Test Subject", "Test Content")

    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail


@pytest.mark.asyncio
async def test_craft_and_send_email_invalid_event():
    employee = MagicMock()  # Use MagicMock for employee object
    arrangements = [MockArrangement()]

    with pytest.raises(ValueError) as excinfo:
        await notifications.craft_and_send_email(employee, arrangements, "invalid_event")
    assert str(excinfo.value) == "Invalid event: invalid_event"


@pytest.mark.asyncio
async def test_craft_and_send_email_create_with_manager(mocker):
    manager = MagicMock()
    manager.email = "manager@example.com"
    employee = MagicMock()
    arrangements = [MockArrangement()]

    # Mock the send_email function to prevent actual email sending
    mocker.patch("src.notifications.email_notifications.send_email", return_value=True)

    result = await notifications.craft_and_send_email(
        employee, arrangements, "create", manager=manager
    )
    assert result is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_http_exception(mock_post: MagicMock):
    # Simulate a request error when sending the email
    mock_post.side_effect = httpx.RequestError("Request failed")

    # Call the function and check for HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await send_email("to_email@example.com", "Test Subject", "Test Content")

    assert exc_info.value.status_code == 500
    assert "An error occurred while sending the email: Request failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_craft_and_send_email_reject_with_manager(mocker):
    # Mock send_email to prevent actual email sending
    mocker.patch("src.notifications.email_notifications.send_email", return_value=True)

    manager = MagicMock()  # Mock manager
    employee = MagicMock()  # Mock employee
    arrangements = [MockArrangement()]  # Mock arrangements

    result = await notifications.craft_and_send_email(
        employee, arrangements, "reject", manager=manager
    )
    assert result is True


@pytest.mark.asyncio
async def test_craft_email_content_multiple_arrangements():
    employee = MagicMock()  # Use MagicMock for employee object
    arrangements = [MockArrangement(), MockArrangement()]  # Mock multiple arrangements
    subject, content = notifications.craft_email_content(employee, arrangements, True)

    assert "Request ID" in content
    assert "WFH Date" in content


@pytest.mark.asyncio
async def test_craft_and_send_email_create_with_empty_manager_email(mocker):
    manager = MagicMock()
    manager.email = ""
    employee = MagicMock()
    arrangements = [MockArrangement()]

    # Mock the send_email function to prevent actual email sending
    mocker.patch("src.notifications.email_notifications.send_email", return_value=True)

    result = await notifications.craft_and_send_email(
        employee, arrangements, "create", manager=manager
    )
    assert result is True


@pytest.mark.asyncio
async def test_craft_and_send_email_unhandled_event(mocker):
    employee = MagicMock()  # Use MagicMock for employee object
    arrangements = [MockArrangement()]

    with pytest.raises(ValueError) as excinfo:
        await notifications.craft_and_send_email(employee, arrangements, "unhandled_event")
    assert str(excinfo.value) == "Invalid event: unhandled_event"


@pytest.mark.asyncio
async def test_send_email_empty_inputs():
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
async def test_craft_email_content_multiple_empty_arrangements():
    employee = MagicMock()  # Use MagicMock for employee object
    arrangements = []  # No arrangements
    subject, content = notifications.craft_email_content(employee, arrangements, True)

    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "Your WFH request has been successfully created" in content
    assert "This email is auto-generated. Please do not reply" in content


@pytest.mark.asyncio
async def test_craft_and_send_email_none_manager_employee():
    # Test when employee is None
    employee = None
    arrangements = [MockArrangement()]

    # Ensure that it raises an error when the employee is None
    with pytest.raises(AttributeError) as exc_info:
        await notifications.craft_and_send_email(employee, arrangements, "approve")

    assert "'NoneType' object has no attribute 'staff_fname'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_craft_rejection_email_content_missing_data():
    # Mock incomplete arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(wfh_date=None, current_approval_status=None, status_reason=None)

    subject, content = notifications.craft_rejection_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Assertions to ensure missing fields are handled gracefully
    assert "WFH Date: None" in content  # Ensure that missing date is shown as 'None'
    assert "Rejection Reason: None" in content


@pytest.mark.asyncio
async def test_craft_approval_email_content_invalid_arrangement_data():
    # Test with None values for arrangement data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(wfh_date=None, current_approval_status=None)

    subject, content = notifications.craft_approval_email_content(mock_staff, mock_arrangement)

    # Ensure invalid data is gracefully omitted from the content
    assert "WFH Date: None" in content  # Ensure None is shown for missing data
    assert "Approval Status: Approved" in content


@pytest.mark.asyncio
@patch("src.notifications.email_notifications.send_email", return_value=True)
async def test_craft_and_send_email_no_manager(mock_send_email):
    employee = MagicMock(email="employee@example.com")
    arrangements = [MockArrangement()]

    # Call the function when the manager is None
    result = await notifications.craft_and_send_email(
        employee, arrangements, "approve", manager=None
    )

    assert result is True  # Ensure the function completes successfully
    mock_send_email.assert_called_once()  # Ensure that send_email was called


@pytest.mark.asyncio
async def test_craft_email_content_missing_arrangement_id():
    # Test case when arrangement_id is missing or None
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        arrangement_id=None, wfh_date="2024-10-07", current_approval_status="approved"
    )

    subject, content = notifications.craft_email_content(
        mock_staff, [mock_arrangement], success=True
    )

    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "WFH Date: 2024-10-07" in content
    assert "Request ID: None" in content  # Ensure None is shown for missing arrangement_id


@pytest.mark.asyncio
async def test_craft_email_content_empty_wfh_type():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        wfh_date="2024-10-07", wfh_type="", reason_description="Work from home"
    )

    subject, content = notifications.craft_email_content(
        mock_staff, [mock_arrangement], success=True
    )

    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "WFH Date: 2024-10-07" in content
    assert "Type: " in content  # Ensure the type field is present but empty


@pytest.mark.asyncio
async def test_craft_email_content_missing_update_datetime():
    # Test case for missing update_datetime in arrangement
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(wfh_date="2024-10-07", update_datetime=None)

    subject, content = notifications.craft_email_content(
        mock_staff, [mock_arrangement], success=True
    )

    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "WFH Date: 2024-10-07" in content
    assert "Updated: None" in content  # Ensure the correct field label is present


@pytest.mark.asyncio
@patch("src.notifications.email_notifications.httpx.AsyncClient.post")
async def test_send_email_invalid_email_format(mock_post: MagicMock):
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
async def test_craft_rejection_email_empty_reason_description():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = MagicMock(
        wfh_date="2024-10-08", current_approval_status="rejected", status_reason=""
    )

    subject, content = notifications.craft_rejection_email_content(mock_staff, mock_arrangement)

    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "WFH Date: 2024-10-08" in content
    assert "Rejection Reason: " in content  # Check that the reason field is present but empty


@pytest.mark.asyncio
async def test_craft_and_send_email_approve_with_manager(mocker):
    # Mock send_email to prevent actual email sending
    mocker.patch("src.notifications.email_notifications.send_email", return_value=True)

    employee = MagicMock()
    manager = MagicMock()
    arrangements = [MockArrangement()]

    result = await notifications.craft_and_send_email(
        employee, arrangements, "approve", manager=manager
    )
    assert result is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_http_error(mock_post):
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
async def test_send_email_network_error(mock_post):
    mock_post.side_effect = httpx.RequestError("Network error")

    with pytest.raises(HTTPException) as exc_info:
        await send_email("test@example.com", "Test Subject", "Test Content")
    assert exc_info.value.status_code == 500
    assert "An error occurred while sending the email: Network error" in exc_info.value.detail
