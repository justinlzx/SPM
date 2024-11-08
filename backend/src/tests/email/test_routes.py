import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

SMTP_USERNAME = os.getenv("SMTP_USERNAME")


@pytest.fixture
def valid_email_data():
    return {"to_email": "test@example.com", "subject": "Test Subject", "content": "Test Content"}


def test_send_email_success(valid_email_data):
    response = client.post("/email/sendemail", data=valid_email_data)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Email sent successfully!",  # Updated to match the actual response
        "sender_email": SMTP_USERNAME,
        "to_email": valid_email_data["to_email"],
        "subject": valid_email_data["subject"],
        "content": valid_email_data["content"],
    }


@pytest.mark.parametrize("field", ["to_email", "subject", "content"])
def test_empty_fields(valid_email_data, field):
    data = valid_email_data.copy()
    data[field] = "   "  # Empty string with whitespace

    response = client.post("/email/sendemail", data=data)

    assert response.status_code == 400
    # Updated assertions to match actual error messages
    expected_messages = {
        "to_email": "Recipient email cannot be empty.",
        "subject": "Subject cannot be empty.",
        "content": "Content cannot be empty.",
    }
    assert response.json()["detail"] == expected_messages[field]


def test_invalid_email():
    data = {
        "to_email": "invalid-email",  # Invalid email format
        "subject": "Test Subject",
        "content": "Test Content",
    }

    response = client.post("/email/sendemail", data=data)

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_missing_fields():
    # Test with missing email
    response = client.post(
        "/email/sendemail", data={"subject": "Test Subject", "content": "Test Content"}
    )
    assert response.status_code == 422  # FastAPI validation error

    # Test with missing subject
    response = client.post(
        "/email/sendemail", data={"to_email": "test@example.com", "content": "Test Content"}
    )
    assert response.status_code == 422

    # Test with missing content
    response = client.post(
        "/email/sendemail", data={"to_email": "test@example.com", "subject": "Test Subject"}
    )
    assert response.status_code == 422


def test_long_content():
    data = {
        "to_email": "test@example.com",
        "subject": "Test Subject",
        "content": "A" * 10000,  # Very long content
    }

    response = client.post("/email/sendemail", data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert response_data["content"] == data["content"]


def test_special_characters():
    data = {
        "to_email": "test@example.com",
        "subject": "Test Subject !@#$%^&*()",
        "content": "Content with special characters: !@#$%^&*()",
    }

    response = client.post("/email/sendemail", data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["subject"] == data["subject"]
    assert response_data["content"] == data["content"]


@patch("src.email.models.EmailModel.send_email")
def test_timeout_error(mock_send_email, valid_email_data):
    # Simulate a TimeoutError
    mock_send_email.side_effect = TimeoutError("Connection timed out")

    response = client.post("/email/sendemail", data=valid_email_data)

    assert response.status_code == 500
    assert response.json()["detail"] == "Connection timed out"


@patch("src.email.models.EmailModel.send_email")
def test_general_exception(mock_send_email, valid_email_data):
    # Simulate a general exception
    mock_send_email.side_effect = Exception("Unexpected error occurred")

    response = client.post("/email/sendemail", data=valid_email_data)

    assert response.status_code == 500
    assert response.json()["detail"] == "Unexpected error occurred"
