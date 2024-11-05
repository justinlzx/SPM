import pytest
from src.email.exceptions import InvalidEmailException


def test_invalid_email_exception_message():
    """Test if the exception message is formatted correctly"""
    test_email = "invalid.email@"
    with pytest.raises(InvalidEmailException) as exc_info:
        raise InvalidEmailException(test_email)

    assert str(exc_info.value) == f"Email '{test_email}' is not in the correct format"


def test_invalid_email_exception_inheritance():
    """Test if InvalidEmailException properly inherits from Exception"""
    test_email = "test@example"
    exception = InvalidEmailException(test_email)
    assert isinstance(exception, Exception)


def test_invalid_email_exception_attributes():
    """Test if the exception instance has the correct attributes"""
    test_email = "incomplete@email."
    exception = InvalidEmailException(test_email)
    assert hasattr(exception, "message")
    assert exception.message == f"Email '{test_email}' is not in the correct format"


@pytest.mark.parametrize(
    "test_email",
    [
        "user@",
        "@domain.com",
        "no_at_sign",
        "multiple@@signs.com",
        ".starts.with.dot@domain.com",
        "ends.with.dot.@domain.com",
        "user@domain.",
        "",
        " @domain.com",
        "user@ domain.com",
    ],
)
def test_invalid_email_exception_various_formats(test_email):
    """Test the exception with various invalid email formats"""
    with pytest.raises(InvalidEmailException) as exc_info:
        raise InvalidEmailException(test_email)

    assert str(exc_info.value) == f"Email '{test_email}' is not in the correct format"
