import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from src.employees.routes import router
from src.app import app
from src.employees import services, exceptions
from src.tests.test_utils import mock_db_session
from src.employees.schemas import EmployeeBase, EmployeePeerResponse
from src.database import get_db  # Import get_db to override the dependency

client = TestClient(app)

app.include_router(router)

# Override the dependency in the app with the mocked db session
app.dependency_overrides[get_db] = mock_db_session  # Now the override should work


def test_get_reporting_manager_and_peer_employees_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting manager and peer employees."""
    # Create mock objects for manager and peer employees
    mock_manager = MagicMock()
    mock_manager.staff_id = 1

    mock_peer_employee = MagicMock()
    mock_peer_employee.staff_id = 2

    # Mock the service functions
    def mock_get_manager_by_subordinate_id(db, staff_id):
        return mock_manager

    def mock_get_subordinates_by_manager_id(db, manager_id):
        return [mock_peer_employee]

    # Patch the service functions with the mocks
    monkeypatch.setattr(
        services, "get_manager_by_subordinate_id", mock_get_manager_by_subordinate_id
    )
    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    # Call the API endpoint
    response = client.get("/manager/peermanager/1")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == 1
    assert len(data["peer_employees"]) == 1
    assert data["peer_employees"][0]["staff_id"] == 2


def test_get_reporting_manager_and_peer_employees_employee_not_found(mock_db_session, monkeypatch):
    """Test scenario where employee is not found."""

    # Mock the service function to raise an exception
    def mock_get_manager_by_subordinate_id(db, staff_id):
        raise exceptions.EmployeeNotFoundException("Employee not found")

    monkeypatch.setattr(
        services, "get_manager_by_subordinate_id", mock_get_manager_by_subordinate_id
    )

    # Call the API endpoint
    response = client.get("/manager/peermanager/999")

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_get_employee_by_staff_id_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting an employee by staff_id."""
    mock_employee = MagicMock()
    mock_employee.staff_id = 1

    def mock_get_employee_by_id(db, staff_id):
        return mock_employee

    monkeypatch.setattr(services, "get_employee_by_id", mock_get_employee_by_id)

    response = client.get("/1")
    assert response.status_code == 200
    assert response.json()["staff_id"] == 1


def test_get_employee_by_staff_id_employee_not_found(mock_db_session, monkeypatch):
    """Test scenario where employee by staff_id is not found."""

    def mock_get_employee_by_id(db, staff_id):
        raise exceptions.EmployeeNotFoundException("Employee not found")

    monkeypatch.setattr(services, "get_employee_by_id", mock_get_employee_by_id)

    response = client.get("/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_get_employee_by_email_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting an employee by email."""
    mock_employee = MagicMock()
    mock_employee.email = "test@example.com"

    def mock_get_employee_by_email(db, email):
        return mock_employee

    monkeypatch.setattr(services, "get_employee_by_email", mock_get_employee_by_email)

    response = client.get("/email/test@example.com")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_get_employee_by_email_not_found(mock_db_session, monkeypatch):
    """Test scenario where employee by email is not found."""

    def mock_get_employee_by_email(db, email):
        raise exceptions.EmployeeNotFoundException("Employee not found")

    monkeypatch.setattr(services, "get_employee_by_email", mock_get_employee_by_email)

    response = client.get("/email/notfound@example.com")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_get_subordinates_by_manager_id_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting subordinates by manager_id."""
    mock_employee = MagicMock()
    mock_employee.staff_id = 2

    def mock_get_subordinates_by_manager_id(db, manager_id):
        return [mock_employee]

    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/employees/1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["staff_id"] == 2


def test_get_subordinates_by_manager_id_manager_not_found(mock_db_session, monkeypatch):
    """Test scenario where manager is not found."""

    def mock_get_subordinates_by_manager_id(db, manager_id):
        raise exceptions.ManagerNotFoundException("Manager not found")

    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/employees/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Manager not found"}
