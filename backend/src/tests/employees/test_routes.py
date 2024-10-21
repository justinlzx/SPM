from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.app import app
from src.database import get_db  # Import get_db to override the dependency
from src.employees import exceptions, services
from src.employees.exceptions import EmployeeNotFoundException, ManagerNotFoundException
from src.employees.routes import router
from src.tests.test_utils import mock_db_session
from src.employees.models import DelegationStatus

client = TestClient(app)

app.include_router(router)

# Override the dependency in the app with the mocked db session
# app.dependency_overrides[get_db] = mock_db_session


def override_get_db():
    return mock_db_session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def mock_employee_service():
    with patch("src.employees.services.get_employee_by_id") as mock:
        yield mock


@pytest.fixture
def mock_send_email():
    with patch("src.employees.routes.send_email") as mock:
        yield mock


def test_get_reporting_manager_and_peer_employees_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting manager and peer employees."""
    # Create mock objects for manager and peer employees with all required fields
    mock_manager = MagicMock()
    mock_manager.staff_id = 1
    mock_manager.staff_fname = "John"
    mock_manager.staff_lname = "Doe"
    mock_manager.dept = "IT"
    mock_manager.position = "Manager"
    mock_manager.country = "USA"
    mock_manager.email = "john.doe@example.com"
    mock_manager.reporting_manager = None
    mock_manager.role = 1

    mock_peer_employee = MagicMock()
    mock_peer_employee.staff_id = 2
    mock_peer_employee.staff_fname = "Jane"
    mock_peer_employee.staff_lname = "Smith"
    mock_peer_employee.dept = "HR"
    mock_peer_employee.position = "Executive"
    mock_peer_employee.country = "USA"
    mock_peer_employee.email = "jane.smith@example.com"
    mock_peer_employee.reporting_manager = 1
    mock_peer_employee.role = 2

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

    # Mock the service function to raise the exception without arguments
    def mock_get_manager_by_subordinate_id(db, staff_id):
        raise exceptions.EmployeeNotFoundException()  # No argument passed

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
    mock_employee.staff_fname = "John"
    mock_employee.staff_lname = "Doe"
    mock_employee.dept = "IT"
    mock_employee.position = "Manager"
    mock_employee.country = "USA"
    mock_employee.email = "john.doe@example.com"
    mock_employee.reporting_manager = None
    mock_employee.role = 1

    def mock_get_employee_by_id(db, staff_id):
        return mock_employee

    monkeypatch.setattr(services, "get_employee_by_id", mock_get_employee_by_id)

    response = client.get("/1")
    assert response.status_code == 200
    assert response.json()["staff_id"] == 1


def test_get_employee_by_staff_id_employee_not_found(mock_db_session, monkeypatch):
    """Test scenario where employee by staff_id is not found."""

    def mock_get_employee_by_id(db, staff_id):
        raise exceptions.EmployeeNotFoundException()  # No argument passed

    monkeypatch.setattr(services, "get_employee_by_id", mock_get_employee_by_id)

    response = client.get("/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_get_employee_by_email_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting an employee by email."""
    mock_employee = MagicMock()
    mock_employee.staff_id = 1
    mock_employee.staff_fname = "John"
    mock_employee.staff_lname = "Doe"
    mock_employee.dept = "IT"
    mock_employee.position = "Manager"
    mock_employee.country = "USA"
    mock_employee.email = "john.doe@example.com"
    mock_employee.reporting_manager = None
    mock_employee.role = 1

    def mock_get_employee_by_email(db, email):
        return mock_employee

    monkeypatch.setattr(services, "get_employee_by_email", mock_get_employee_by_email)

    response = client.get("/email/john.doe@example.com")
    assert response.status_code == 200
    assert response.json()["email"] == "john.doe@example.com"


def test_get_employee_by_email_not_found(mock_db_session, monkeypatch):
    """Test scenario where employee by email is not found."""

    def mock_get_employee_by_email(db, email):
        raise exceptions.EmployeeNotFoundException()  # No argument passed

    monkeypatch.setattr(services, "get_employee_by_email", mock_get_employee_by_email)

    response = client.get("/email/notfound@example.com")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_get_subordinates_by_manager_id_success(mock_db_session, monkeypatch):
    """Test the success scenario of getting subordinates by manager_id."""
    mock_employee = MagicMock()
    mock_employee.staff_id = 2
    mock_employee.staff_fname = "Jane"
    mock_employee.staff_lname = "Smith"
    mock_employee.dept = "HR"
    mock_employee.position = "Executive"
    mock_employee.country = "USA"
    mock_employee.email = "jane.smith@example.com"
    mock_employee.reporting_manager = 1
    mock_employee.role = 2

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
        raise exceptions.ManagerNotFoundException()  # No argument passed

    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/employees/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Manager not found"}


def test_get_reporting_manager_and_peer_employees_partial_data(mock_db_session, monkeypatch):
    """Test scenario where manager and peer employees data is complete but minimal."""
    # Mock manager with all required fields
    mock_manager = MagicMock()
    mock_manager.staff_id = 1
    mock_manager.staff_fname = "John"
    mock_manager.staff_lname = "Doe"  # Required field
    mock_manager.dept = "IT"  # Required field
    mock_manager.position = "Manager"  # Required field
    mock_manager.country = "USA"
    mock_manager.email = "john.doe@example.com"
    mock_manager.reporting_manager = None
    mock_manager.role = 1

    # Mock peer employee with all required fields
    mock_peer_employee = MagicMock()
    mock_peer_employee.staff_id = 2
    mock_peer_employee.staff_fname = "Jane"
    mock_peer_employee.staff_lname = "Smith"  # Required field
    mock_peer_employee.dept = "HR"  # Required field
    mock_peer_employee.position = "Executive"  # Required field
    mock_peer_employee.country = "USA"
    mock_peer_employee.email = "jane.smith@example.com"
    mock_peer_employee.reporting_manager = 1
    mock_peer_employee.role = 2

    def mock_get_manager_by_subordinate_id(db, staff_id):
        return mock_manager

    def mock_get_subordinates_by_manager_id(db, manager_id):
        return [mock_peer_employee]

    monkeypatch.setattr(
        services, "get_manager_by_subordinate_id", mock_get_manager_by_subordinate_id
    )
    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/peermanager/1")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == 1
    assert len(data["peer_employees"]) == 1
    assert data["peer_employees"][0]["staff_id"] == 2


def test_get_employee_by_invalid_staff_id_format(mock_db_session):
    """Test scenario where the staff_id is not a valid integer."""
    response = client.get("/abc")  # Pass an invalid staff_id format (non-integer)

    # Assertions
    assert response.status_code == 422  # 422 is for validation errors
    assert any("integer" in error["msg"] for error in response.json()["detail"])


def test_get_subordinates_by_manager_id_no_subordinates(mock_db_session, monkeypatch):
    """Test scenario where manager has no subordinates."""

    def mock_get_subordinates_by_manager_id(db, manager_id):
        return []  # Empty list of subordinates

    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/employees/1")
    assert response.status_code == 200
    assert response.json() == []  # No subordinates


def test_get_subordinates_by_manager_id_multiple_subordinates(mock_db_session, monkeypatch):
    """Test scenario where multiple subordinates are returned."""

    # Mock subordinates
    mock_employee_1 = MagicMock()
    mock_employee_1.staff_id = 2
    mock_employee_1.staff_fname = "Jane"
    mock_employee_1.staff_lname = "Smith"
    mock_employee_1.dept = "HR"
    mock_employee_1.position = "Executive"
    mock_employee_1.country = "USA"
    mock_employee_1.email = "jane.smith@example.com"
    mock_employee_1.reporting_manager = 1
    mock_employee_1.role = 2

    mock_employee_2 = MagicMock()
    mock_employee_2.staff_id = 3
    mock_employee_2.staff_fname = "Mike"
    mock_employee_2.staff_lname = "Johnson"
    mock_employee_2.dept = "IT"
    mock_employee_2.position = "Engineer"
    mock_employee_2.country = "USA"
    mock_employee_2.email = "mike.johnson@example.com"
    mock_employee_2.reporting_manager = 1
    mock_employee_2.role = 2

    def mock_get_subordinates_by_manager_id(db, manager_id):
        return [mock_employee_1, mock_employee_2]

    monkeypatch.setattr(
        services, "get_subordinates_by_manager_id", mock_get_subordinates_by_manager_id
    )

    response = client.get("/manager/employees/1")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["staff_id"] == 2
    assert data[1]["staff_id"] == 3


def test_get_subordinates_by_manager_id_invalid_format(mock_db_session):
    """Test scenario where the staff_id is not a valid integer."""

    response = client.get("/manager/employees/abc")  # Invalid staff_id

    # Assertions
    assert response.status_code == 422  # Pydantic validation error for invalid format
    assert any("integer" in error["msg"] for error in response.json()["detail"])


def test_get_employee_by_email_invalid_format(mock_db_session):
    """Test scenario where the email format is invalid."""

    response = client.get("/email/invalid-email-format")

    # Assertions
    assert response.status_code == 422  # Pydantic validation error for invalid email
    assert any("email" in error["msg"] for error in response.json()["detail"])


def test_get_reporting_manager_and_peer_employees_manager_not_found(mock_db_session, monkeypatch):
    """Test scenario where manager is not found."""

    # Mock the service function to raise ManagerNotFoundException
    def mock_get_manager_by_subordinate_id(db, staff_id):
        raise exceptions.ManagerNotFoundException()  # No argument passed

    monkeypatch.setattr(
        services, "get_manager_by_subordinate_id", mock_get_manager_by_subordinate_id
    )

    # Call the API endpoint
    response = client.get("/manager/peermanager/1")

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "Manager not found"}


def test_get_reporting_manager_and_peer_employees_self_reporting(mock_db_session, monkeypatch):
    """Test scenario where an employee reports to themselves."""

    # Create a mock manager who reports to themselves
    mock_manager = MagicMock()
    mock_manager.staff_id = 1
    mock_manager.staff_fname = "John"  # Use real string values
    mock_manager.staff_lname = "Doe"  # Use real string values
    mock_manager.dept = "IT"
    mock_manager.position = "Manager"
    mock_manager.country = "USA"
    mock_manager.email = "john.doe@example.com"
    mock_manager.reporting_manager = 1  # Self-reporting
    mock_manager.role = 1

    mock_peer_employee = MagicMock()
    mock_peer_employee.staff_id = 2
    mock_peer_employee.staff_fname = "Jane"
    mock_peer_employee.staff_lname = "Smith"
    mock_peer_employee.dept = "HR"
    mock_peer_employee.position = "Executive"
    mock_peer_employee.country = "USA"
    mock_peer_employee.email = "jane.smith@example.com"
    mock_peer_employee.reporting_manager = 1
    mock_peer_employee.role = 2

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
    assert data["manager_id"] == 1  # The employee should still have themselves as the manager
    assert len(data["peer_employees"]) == 1
    assert data["peer_employees"][0]["staff_id"] == 2


def test_get_reporting_manager_and_peer_employees_auto_approve_jack_sim(mock_db_session):
    """Test the auto-approve scenario for Jack Sim (staff_id=130002)."""

    response = client.get("/manager/peermanager/130002")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] is None
    assert data["peer_employees"] == []


def test_get_reporting_manager_and_peer_employees_manager_none(mock_db_session, monkeypatch):
    """Test the scenario where no manager is found (manager is None)."""

    # Mock the service function to return None for the manager
    def mock_get_manager_by_subordinate_id(db, staff_id):
        return None  # No manager found

    monkeypatch.setattr(
        services, "get_manager_by_subordinate_id", mock_get_manager_by_subordinate_id
    )

    # Call the API endpoint
    response = client.get("/manager/peermanager/1")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] is None
    assert data["peer_employees"] == []


def test_delegate_manager_success(mock_db_session, mock_employee_service, mock_send_email):
    # Arrange: Simulate no existing delegation by returning None for all queries
    mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    # Mock the new delegation creation
    mock_new_delegation = MagicMock()
    mock_new_delegation.manager_id = 140001
    mock_new_delegation.delegate_manager_id = 150008
    mock_new_delegation.status_of_delegation = DelegationStatus.pending
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.side_effect = lambda x: setattr(x, "id", 1)

    # Mock employee service
    mock_employee_service.return_value = MagicMock(email="test@example.com")

    # Override the employee service dependency
    with patch(
        "src.employees.services.get_employee_by_id", return_value=mock_employee_service.return_value
    ):
        # Act: Pass delegate_manager_id as a query parameter
        response = client.put("/manager/delegate/140001?delegate_manager_id=150008")

    # Assert: Validate response and email sending
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}. Response: {response.json()}"
    assert response.json()["status_of_delegation"] == DelegationStatus.pending.value
    mock_send_email.assert_called()


def test_delegate_manager_already_exists(mock_db_session):
    # Arrange: Simulate an existing delegation
    mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = (
        MagicMock()
    )

    # Act: Pass delegate_manager_id as a query parameter
    response = client.put("/manager/delegate/140001?delegate_manager_id=150008")

    # Assert: Expect a 400 error due to existing delegation
    assert (
        response.status_code == 400
    ), f"Unexpected status code: {response.status_code}. Response: {response.json()}"
    assert (
        response.json()["detail"]
        == "Delegation already exists for either the manager or delegatee."
    )


def test_update_delegation_status_accept(mock_db_session, mock_employee_service, mock_send_email):
    # Arrange: Simulate a pending delegation
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(
        manager_id=140001, delegate_manager_id=150008, status_of_delegation="pending"
    )
    mock_employee_service.return_value = MagicMock(email="test@example.com")  # Mock employee email

    # Act: Pass the correct status as a query parameter
    response = client.put("/manager/delegate/150008/status?status=accepted")

    # Assert: Check that the delegation status is updated and emails are sent
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}. Response: {response.json()}"
    assert response.json()["status_of_delegation"] == "accepted"
    mock_send_email.assert_called()  # Ensure emails are sent


def test_update_delegation_status_reject(mock_db_session, mock_employee_service, mock_send_email):
    # Arrange: Simulate a pending delegation
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(
        manager_id=140001, delegate_manager_id=150008, status_of_delegation="pending"
    )
    mock_employee_service.return_value = MagicMock(email="test@example.com")  # Mock employee email

    # Act: Pass the correct status as a query parameter
    response = client.put("/manager/delegate/150008/status?status=rejected")

    # Assert: Check that the delegation status is updated and emails are sent
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}. Response: {response.json()}"
    assert response.json()["status_of_delegation"] == "rejected"
    mock_send_email.assert_called()  # Ensure emails are sent


def test_undelegate_manager_success(mock_db_session, mock_employee_service, mock_send_email):
    # Arrange: Simulate an accepted delegation
    mock_delegation = MagicMock(
        manager_id=140001,
        delegate_manager_id=150008,
        status_of_delegation=DelegationStatus.accepted,
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_delegation

    # Mock employee service
    mock_employee_service.return_value = MagicMock(email="test@example.com")

    # Mock the update of arrangements
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    # Override the employee service dependency
    with patch(
        "src.employees.services.get_employee_by_id", return_value=mock_employee_service.return_value
    ):
        # Act: Call the undelegate endpoint
        response = client.put("/manager/undelegate/140001")

    # Assert: Check that the delegation is undelegated and emails are sent
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}. Response: {response.json()}"
    assert response.json()["status_of_delegation"] == DelegationStatus.undelegated.value
    mock_send_email.assert_called()

    # Verify that the status was updated in the mock
    assert mock_delegation.status_of_delegation == DelegationStatus.undelegated


def test_undelegate_manager_invalid_status(mock_db_session):
    # Arrange: Simulate a pending delegation
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(
        manager_id=140001, delegate_manager_id=150008, status_of_delegation="pending"
    )

    # Act: Call the undelegate endpoint
    response = client.put("/manager/undelegate/140001")

    # Assert: Expect a 400 error since the delegation is not yet accepted
    assert response.status_code == 400
    assert response.json()["detail"] == "Delegation must be approved to undelegate."
