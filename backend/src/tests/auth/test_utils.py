import pytest
from unittest.mock import patch
from datetime import timedelta, datetime, timezone
import hashlib
import jwt
from src.auth.utils import hash_password, verify_password, generate_JWT


# Test for hash_password function
def test_hash_password():
    # Set up test data
    password = "testpassword"
    salt = "randomsalt"

    # Hash the password
    hashed = hash_password(password, salt)

    # Verify that the hashed password matches the expected SHA-256 hash
    expected_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    assert hashed == expected_hash


# Test for verify_password function
def test_verify_password():
    # Set up test data
    password = "testpassword"
    salt = "randomsalt"

    # Hash the password to create a stored hash
    stored_hash = hash_password(password, salt)

    # Verify the password with correct input
    assert verify_password(password, stored_hash, salt)

    # Verify the password with incorrect input
    assert not verify_password("wrongpassword", stored_hash, salt)


# Test for generate_JWT function
@patch("src.auth.utils.TOKEN_SECRET", "test_secret")
def test_generate_JWT():
    # Set up test data
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=5)

    # Mock datetime to control the 'now' time for testing
    with patch("src.auth.utils.datetime") as mock_datetime:
        # Set a fixed UTC datetime to avoid discrepancies
        mock_now = datetime(2024, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        # Generate JWT token
        token = generate_JWT(data, expires_delta)

        # Decode the JWT token to verify its content
        decoded_data = jwt.decode(token, "test_secret", algorithms=["HS256"])

        # Verify the token data
        assert decoded_data["sub"] == data["sub"]
        assert "exp" in decoded_data

        # Expected expiration time based on the fixed datetime
        expected_expiration = mock_now + expires_delta

        # Compare the expiration times as UTC
        assert datetime.fromtimestamp(decoded_data["exp"], tz=timezone.utc) == expected_expiration

    # Test default expiration (15 minutes)
    with patch("src.auth.utils.datetime") as mock_datetime:
        mock_now = datetime(2024, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        # Generate JWT token with default expiration
        default_token = generate_JWT(data)
        default_decoded_data = jwt.decode(default_token, "test_secret", algorithms=["HS256"])

        # Default expiration is 15 minutes
        default_expected_expiration = mock_now + timedelta(minutes=15)
        assert (
            datetime.fromtimestamp(default_decoded_data["exp"], tz=timezone.utc)
            == default_expected_expiration
        )
