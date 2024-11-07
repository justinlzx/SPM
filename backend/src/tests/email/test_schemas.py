import pytest
from pydantic import ValidationError
from typing import Any, Dict

from src.email.schemas import EmailSchema


def create_valid_email_data() -> Dict[str, Any]:
    """Helper function to create valid email data"""
    return {
        "sender_email": "sender@example.com",
        "to_email": "recipient@example.com",
        "subject": "Test Subject",
        "content": "Test Content",
    }


def test_valid_email_schema():
    """Test creation of EmailSchema with valid data"""
    email_data = create_valid_email_data()
    email = EmailSchema(**email_data)

    assert email.sender_email == email_data["sender_email"]
    assert email.to_email == email_data["to_email"]
    assert email.subject == email_data["subject"]
    assert email.content == email_data["content"]


def test_invalid_sender_email():
    """Test validation error for invalid sender email"""
    email_data = create_valid_email_data()
    email_data["sender_email"] = "invalid-email"

    with pytest.raises(ValidationError) as exc_info:
        EmailSchema(**email_data)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("sender_email",)
    assert "value is not a valid email address" in errors[0]["msg"]


def test_invalid_recipient_email():
    """Test validation error for invalid recipient email"""
    email_data = create_valid_email_data()
    email_data["to_email"] = "not-an-email"

    with pytest.raises(ValidationError) as exc_info:
        EmailSchema(**email_data)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("to_email",)
    assert "value is not a valid email address" in errors[0]["msg"]


def test_empty_subject():
    """Test that empty subject is allowed"""
    email_data = create_valid_email_data()
    email_data["subject"] = ""

    email = EmailSchema(**email_data)
    assert email.subject == ""


def test_empty_content():
    """Test that empty content is allowed"""
    email_data = create_valid_email_data()
    email_data["content"] = ""

    email = EmailSchema(**email_data)
    assert email.content == ""


def test_missing_required_fields():
    """Test validation error when required fields are missing"""
    with pytest.raises(ValidationError) as exc_info:
        EmailSchema()

    errors = exc_info.value.errors()
    assert len(errors) == 4  # All fields are required
    field_names = {error["loc"][0] for error in errors}
    assert field_names == {"sender_email", "to_email", "subject", "content"}


@pytest.mark.parametrize("email_field", ["sender_email", "to_email"])
def test_email_normalization(email_field):
    """Test that email addresses are properly normalized"""
    email_data = create_valid_email_data()
    email_data[email_field] = "Test.User@EXAMPLE.COM"

    email = EmailSchema(**email_data)
    assert getattr(email, email_field) == "Test.User@example.com"
