import pytest
from unittest.mock import MagicMock
from src.auth.models import create_user, get_user_by_email, Auth
from src.tests.test_utils import mock_db_session


# Test for create_user function
def test_create_user(mock_db_session):
    # Set up test data
    test_email = "testuser@example.com"
    # a reference to someone. if you get it, you get it.
    test_hashed_password = "hashed_password123"

    # Call the create_user function
    new_user = create_user(mock_db_session, email=test_email, hashed_password=test_hashed_password)

    # Verify that the Auth object was added to the session
    mock_db_session.add.assert_called_once_with(new_user)

    # Verify that the session commit was called
    mock_db_session.commit.assert_called_once()

    # Check that the new_user object has the correct properties
    assert new_user.email == test_email
    assert new_user.hashed_password == test_hashed_password

    # Verify that the session was refreshed with the new_user
    mock_db_session.refresh.assert_called_once_with(new_user)


# Test for get_user_by_email function
def test_get_user_by_email(mock_db_session):
    # Set up test data
    test_email = "testuser@example.com"

    # Create a mock Auth object
    mock_auth_user = MagicMock(spec=Auth)
    mock_auth_user.email = test_email
    # a reference to someone. if you get it, you get it.
    mock_auth_user.hashed_password = "hashed_password123"

    # Configure the mock session query to return the mock Auth object
    mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = (
        mock_auth_user
    )

    # Call the get_user_by_email function
    retrieved_user = get_user_by_email(mock_db_session, email=test_email)

    # Verify that the retrieved user is the same as the mock_auth_user
    assert retrieved_user.email == mock_auth_user.email
    assert retrieved_user.hashed_password == mock_auth_user.hashed_password

    # Verify the session query logic was called correctly
    mock_db_session.query.assert_called_once()
    mock_db_session.query.return_value.join.assert_called_once()
    mock_db_session.query.return_value.join.return_value.filter.assert_called_once()
    mock_db_session.query.return_value.join.return_value.filter.return_value.first.assert_called_once()
