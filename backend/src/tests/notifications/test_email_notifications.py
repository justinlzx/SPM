import os
from unittest.mock import MagicMock, patch
import pytest
from dotenv import load_dotenv
from fastapi import HTTPException
from httpx import RequestError, Response
from src.arrangements.schemas import ArrangementLog
from src.arrangements.models import LatestArrangement
from src.notifications.email_notifications import (
    craft_approval_email_content,
    craft_email_content,
    craft_rejection_email_content,
    fetch_manager_info,
    send_email,
)

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_success(mock_get):
    # Mock response data
    mock_response_data = {"manager_id": 1, "manager_name": "John Doe"}

    # Simulate the mock to return a successful response
    mock_get.return_value.json = MagicMock(return_value=mock_response_data)
    mock_get.return_value.status_code = 200

    # Call the function
    result = await fetch_manager_info(staff_id=123)

    # Assertions
    assert result == mock_response_data
    mock_get.assert_called_once_with(f"{BASE_URL}/employees/manager/peermanager/123")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_failure(mock_get):
    # Set the mock to return an unsuccessful response
    mock_get.return_value.status_code = 404
    mock_get.return_value.text = "Not Found"

    # Call the function and check for HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await fetch_manager_info(staff_id=123)

    assert exc_info.value.status_code == 404
    assert "Error fetching manager info" in exc_info.value.detail


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_success(mock_post):
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
async def test_send_email_failure(mock_post):
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
async def test_craft_email_content():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = LatestArrangement(
        arrangement_id=1,
        wfh_date="2024-10-07",
        current_approval_status="pending",
        wfh_type="full",
        reason_description="Work from home for personal reasons",
        batch_id="1001",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
    )

    subject, content = craft_email_content(
        employee=mock_staff, arrangements=[mock_arrangement], success=True
    )

    # Assertions for content
    assert "[All-In-One] Successful Creation of WFH Request" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    assert "Approval Status: pending" in content


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

    subject, content = craft_approval_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Approved" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    assert "Approval Reason: Need to work remotely" in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = LatestArrangement(  # Use LatestArrangement
        arrangement_id=3,
        wfh_date="2024-10-08",
        wfh_type="am",
        reason_description="Unable to come to office",
        batch_id="1003",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
        current_approval_status="rejected",  # Field from LatestArrangement
        status_reason="Not enough reason provided",  # Status reason
    )

    subject, content = craft_rejection_email_content(
        employee=mock_staff, arrangement=mock_arrangement
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-08" in content
    assert "Rejection Reason: Not enough reason provided" in content


@pytest.mark.asyncio
async def test_craft_email_content_failure():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    error_message = "Some error occurred"

    subject, content = craft_email_content(
        employee=mock_staff, arrangements=[], success=False, error_message=error_message
    )

    assert subject == "[All-In-One] Unsuccessful Creation of WFH Request"
    assert "Unfortunately, there was an error processing your WFH request" in content
    assert error_message in content
