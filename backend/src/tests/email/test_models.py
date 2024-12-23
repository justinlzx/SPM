# tests/test_email_model.py

import os
import smtplib
from unittest.mock import MagicMock, patch

import pytest
from src.email.exceptions import InvalidEmailException
from src.email.models import EmailModel

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


@pytest.fixture
def email_data():
    return {
        "sender_email": "sender@example.com",
        "to_email": "recipient@example.com",
        "subject": "Test Subject",
        "content": "This is a test email.",
    }


@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP") as mock_smtp:
        yield mock_smtp


@pytest.fixture
def mock_environ():
    env_vars = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": SMTP_USERNAME,
        "SMTP_PASSWORD": SMTP_PASSWORD,
    }
    with patch.dict("os.environ", env_vars):
        yield


@pytest.mark.asyncio
async def test_send_real_email_success(email_data, mock_environ):
    email = EmailModel(
        sender_email=email_data["sender_email"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        content=email_data["content"],
    )

    result = await email.send_email()

    assert result == {"message": "Email sent successfully!"}


@pytest.mark.asyncio
async def test_send_email_success(email_data, mock_smtp, mock_environ):
    # Mock the SMTP instance
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    email = EmailModel(
        sender_email=email_data["sender_email"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        content=email_data["content"],
    )

    result = await email.send_email()

    # Assertions
    assert result == {"message": "Email sent successfully!"}
    mock_smtp.assert_called_once_with("smtp.gmail.com", "587")
    mock_server.starttls.assert_called_once()
    mock_server.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(email_data, mock_smtp, mock_environ):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    mock_server.sendmail.side_effect = smtplib.SMTPException("SMTP error")

    email = EmailModel(
        sender_email=email_data["sender_email"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        content=email_data["content"],
    )

    with pytest.raises(smtplib.SMTPException):
        await email.send_email()


@pytest.mark.asyncio
async def test_send_email_smtp_login_failure(email_data, mock_smtp, mock_environ):
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server

    email = EmailModel(
        sender_email=email_data["sender_email"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        content=email_data["content"],
    )

    with pytest.raises(smtplib.SMTPAuthenticationError):
        await email.send_email()


def test_email_with_invalid_email_format():

    # Test invalid sender email
    with pytest.raises(InvalidEmailException):
        EmailModel("invalid_sender_email", "user@example.com", "Subject", "Content")

    # Test invalid recipient email
    with pytest.raises(InvalidEmailException):
        EmailModel("user@example.com", "invalid_recipient_email", "Subject", "Content")


@pytest.mark.asyncio
async def test_smtp_connection_timeout(email_data, mock_smtp):
    mock_smtp.side_effect = TimeoutError("Connection timed out")

    email = EmailModel(
        sender_email=email_data["sender_email"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        content=email_data["content"],
    )

    with pytest.raises(TimeoutError):
        await email.send_email()
