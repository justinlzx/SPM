import pytest
from unittest.mock import patch, MagicMock
from httpx import Response, RequestError  # Add RequestError for exception handling
from fastapi import HTTPException
from src.notifications.email_notifications import (
    fetch_manager_info,
    craft_email_content,
    craft_approval_email_content,
    craft_rejection_email_content,
    send_email,
)
from src.arrangements.schemas import ArrangementLog


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_success(mock_get):
    # Mock response data
    mock_response_data = {"manager_id": 1, "manager_name": "John Doe"}

    # Set the mock to return a successful response
    mock_get.return_value = Response(status_code=200, json=mock_response_data)

    # Call the function
    result = await fetch_manager_info(staff_id=123)

    # Assertions
    assert result == mock_response_data
    mock_get.assert_called_once_with("http://localhost:8000/employee/manager/peermanager/123")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_failure(mock_get):
    # Set the mock to return an unsuccessful response
    mock_get.return_value = Response(status_code=404, text="Not Found")

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

    # Set the mock to return a successful response
    mock_post.return_value = Response(status_code=200, json=mock_response_data)

    # Call the function
    result = await send_email(
        to_email="test@example.com", subject="Test Subject", content="Test Content"
    )

    # Assertions
    assert result == mock_response_data
    mock_post.assert_called_once_with(
        "http://localhost:8000/email/sendemail",
        data={"to_email": "test@example.com", "subject": "Test Subject", "content": "Test Content"},
    )


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_failure(mock_post):
    # Set the mock to return an unsuccessful response
    mock_post.return_value = Response(status_code=500, text="Internal Server Error")

    # Call the function and check for HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await send_email(
            to_email="test@example.com", subject="Test Subject", content="Test Content"
        )

    assert exc_info.value.status_code == 500
    assert (
        exc_info.value.detail == "Internal Server Error"
    )  # Adjust the assertion to match the error message


@pytest.mark.asyncio
async def test_craft_email_content():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = ArrangementLog(
        arrangement_id=1,
        wfh_date="2024-10-07",
        approval_status="pending",  # Must match expected literals
        wfh_type="full",  # Must match expected literals
        reason_description="Work from home for personal reasons",
        batch_id="1001",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
    )

    subject, content = await craft_email_content(
        staff=mock_staff, response_data=[mock_arrangement], success=True
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
        wfh_type="full",  # Must match expected literals
        reason_description="Need to work remotely",
        batch_id="1002",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
        approval_status="approved",  # Must match expected literals
    )

    subject, content = await craft_approval_email_content(
        staff=mock_staff, arrangement=mock_arrangement, reason="Approved by manager"
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Approved" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-07" in content
    assert "Approval Reason: Approved by manager" in content


@pytest.mark.asyncio
async def test_craft_rejection_email_content():
    # Mock arrangement and staff data
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_arrangement = ArrangementLog(
        arrangement_id=3,
        wfh_date="2024-10-08",
        wfh_type="am",  # Must match expected literals
        reason_description="Unable to come to office",
        batch_id="1003",
        update_datetime="2024-10-06T12:00:00",
        requester_staff_id="12345",
        approval_status="rejected",  # Must match expected literals
    )

    subject, content = await craft_rejection_email_content(
        staff=mock_staff, arrangement=mock_arrangement, reason="Not enough reason provided"
    )

    # Assertions for content
    assert "[All-In-One] Your WFH Request Has Been Rejected" in subject
    assert "Dear Jane Doe" in content
    assert "WFH Date: 2024-10-08" in content
    assert "Rejection Reason: Not enough reason provided" in content


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_manager_info_request_error(mock_get):
    # Simulate a request error
    mock_get.side_effect = RequestError("Request failed")

    with pytest.raises(HTTPException) as exc_info:
        await fetch_manager_info(staff_id=1)

    assert exc_info.value.status_code == 500
    assert "An error occurred while fetching manager info" in exc_info.value.detail


@pytest.mark.asyncio
async def test_craft_email_content_failure():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    error_message = "Some error occurred"

    subject, content = await craft_email_content(
        staff=mock_staff, response_data=[], success=False, error_message=error_message
    )

    assert subject == "[All-In-One] Unsuccessful Creation of WFH Request"
    assert "Unfortunately, there was an error processing your WFH request" in content
    assert error_message in content


@pytest.mark.asyncio
async def test_craft_email_content_for_manager():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_manager = MagicMock(staff_fname="John", staff_lname="Smith")
    mock_arrangement = MagicMock(
        arrangement_id=1,
        wfh_date="2024-10-07",
        approval_status="approved",
        wfh_type="full",
        reason_description="Work from home",
        batch_id="1001",
        update_datetime="2024-10-06T12:00:00",
    )

    subject, content = await craft_email_content(
        staff=mock_staff, response_data=[mock_arrangement], is_manager=True, manager=mock_manager
    )

    assert subject == "[All-In-One] Your Staff Created a WFH Request"
    assert f"Dear {mock_manager.staff_fname} {mock_manager.staff_lname}" in content
    assert (
        f"{mock_staff.staff_fname} {mock_staff.staff_lname}, one of your staff members" in content
    )


@pytest.mark.asyncio
async def test_craft_approval_email_content_for_manager():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_manager = MagicMock(staff_fname="John", staff_lname="Smith")
    mock_arrangement = MagicMock(
        arrangement_id=2,
        wfh_date="2024-10-07",
        wfh_type="full",
        reason_description="Need to work remotely",
        batch_id="1002",
        update_datetime="2024-10-06T12:00:00",
    )

    subject, content = await craft_approval_email_content(
        staff=mock_staff,
        arrangement=mock_arrangement,
        reason="Approved",
        is_manager=True,
        manager=mock_manager,
    )

    assert subject == "[All-In-One] You Have Approved a WFH Request"
    assert f"Dear {mock_manager.staff_fname} {mock_manager.staff_lname}" in content
    assert (
        f"You have successfully approved a WFH request for {mock_staff.staff_fname} {mock_staff.staff_lname}"
        in content
    )


@pytest.mark.asyncio
async def test_craft_rejection_email_content_for_manager():
    mock_staff = MagicMock(staff_fname="Jane", staff_lname="Doe")
    mock_manager = MagicMock(staff_fname="John", staff_lname="Smith")
    mock_arrangement = MagicMock(
        arrangement_id=3,
        wfh_date="2024-10-08",
        wfh_type="full",
        reason_description="Unable to come to office",
        batch_id="1003",
        update_datetime="2024-10-06T12:00:00",
    )

    subject, content = await craft_rejection_email_content(
        staff=mock_staff,
        arrangement=mock_arrangement,
        reason="Rejected",
        is_manager=True,
        manager=mock_manager,
    )

    assert subject == "[All-In-One] You Have Rejected a WFH Request"
    assert f"Dear {mock_manager.staff_fname} {mock_manager.staff_lname}" in content
    assert (
        f"You have rejected a WFH request for {mock_staff.staff_fname} {mock_staff.staff_lname}"
        in content
    )


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_email_request_error(mock_post):
    # Simulate a request error
    mock_post.side_effect = RequestError("Request failed")

    with pytest.raises(HTTPException) as exc_info:
        await send_email(
            to_email="test@example.com", subject="Test Subject", content="Test Content"
        )

    assert exc_info.value.status_code == 500
    assert "An error occurred while sending the email" in exc_info.value.detail
