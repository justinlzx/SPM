import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.auth.routes import router as auth_router
from src.auth.utils import hash_password
from src.auth.models import Auth
from src.employees.models import Employee
from src.app import app
from src.tests.test_utils import mock_db_session as mock_db_session_fixture
from src.database import get_db

app.include_router(auth_router)

client = TestClient(app)


# Override the get_db dependency with the mocked session generator
@pytest.fixture
def override_get_db(mock_db_session_fixture):
    def _override_get_db():
        yield mock_db_session_fixture

    return _override_get_db


def test_login_successful(override_get_db, mock_db_session_fixture):
    app.dependency_overrides[get_db] = override_get_db

    email = "testuser@example.com"
    password = "testpassword"
    salt = email.lower()
    hashed_password = hash_password(password, salt)

    # Mock the Auth and Employee objects
    mock_auth_user = Auth(email=email, hashed_password=hashed_password)
    mock_employee = Employee(
        email=email,
        staff_id="S12345",
        staff_fname="John",
        staff_lname="Doe",
        dept="Engineering",
        position="Engineer",
        country="USA",
        reporting_manager="Manager",
        role="Staff",
    )

    mock_db_session_fixture.query.return_value.filter.return_value.first.side_effect = [
        mock_auth_user,  # Query for the Auth table
        mock_employee,  # Query for the Employee table
    ]

    response = client.post("/login", data={"email": email, "password": password})

    assert response.status_code == 200

    response_json = response.json()
    assert response_json["message"] == "Login successful"
    assert "access_token" in response_json["data"]
    assert response_json["data"]["email"] == email
    assert response_json["data"]["employee_info"]["staff_id"] == mock_employee.staff_id
    assert response_json["data"]["employee_info"]["first_name"] == mock_employee.staff_fname

    app.dependency_overrides = {}


def test_login_invalid_password(override_get_db, mock_db_session_fixture):
    app.dependency_overrides[get_db] = override_get_db

    email = "testuser@example.com"
    correct_password = "correctpassword"
    wrong_password = "wrongpassword"
    salt = email.lower()
    hashed_password = hash_password(correct_password, salt)

    # Mock the Auth object
    mock_auth_user = Auth(email=email, hashed_password=hashed_password)

    # Mock return value for querying the database
    mock_db_session_fixture.query.return_value.filter.return_value.first.return_value = (
        mock_auth_user
    )

    # Make the API call with wrong password
    response = client.post("/login", data={"email": email, "password": wrong_password})

    # Assert that the response returns a 400 status code for invalid credentials
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"

    app.dependency_overrides = {}


def test_login_user_not_found(override_get_db, mock_db_session_fixture):
    app.dependency_overrides[get_db] = override_get_db

    email = "nonexistent@example.com"

    # Mock return value for querying the database (user not found)
    mock_db_session_fixture.query.return_value.filter.return_value.first.return_value = None

    # Make the API call
    response = client.post("/login", data={"email": email, "password": "any_password"})

    # Assert that the response returns a 400 status code for invalid credentials
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"

    app.dependency_overrides = {}


def test_login_employee_not_found(override_get_db, mock_db_session_fixture):
    app.dependency_overrides[get_db] = override_get_db

    email = "testuser@example.com"
    password = "testpassword"
    salt = email.lower()
    hashed_password = hash_password(password, salt)

    # Mock the Auth object
    mock_auth_user = Auth(email=email, hashed_password=hashed_password)

    # Mock return values for querying the database
    mock_db_session_fixture.query.return_value.filter.return_value.first.side_effect = [
        mock_auth_user,  # Auth user found
        None,  # Employee not found
    ]

    # Make the API call
    response = client.post("/login", data={"email": email, "password": password})

    # Assert that the response returns a 404 status code for employee not found
    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"

    app.dependency_overrides = {}
