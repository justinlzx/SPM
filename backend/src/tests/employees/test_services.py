from unittest.mock import MagicMock, patch

import pytest
from src.employees import exceptions, models, services


# Mock Employee fixture
@pytest.fixture
def mock_employee():
    return models.Employee(staff_id=1, email="test@example.com", reporting_manager=101)


def test_get_manager_by_employee_staff_id(mock_db_session, mock_employee):
    # Arrange: Mock the employee's manager
    mock_employee.manager = MagicMock(staff_id=101)

    # Patch the `get_employee_by_id` function
    with patch("src.employees.services.get_employee_by_id", return_value=mock_employee):
        # Act: Call the service function
        manager = services.get_manager_by_subordinate_id(mock_db_session, 1)

        # Assert: Check if the correct manager is returned
        assert manager.staff_id == 101

    # Test case when employee reports to themselves (manager is None)
    mock_employee.manager = mock_employee  # Employee reports to themselves

    with patch("src.employees.services.get_employee_by_id", return_value=mock_employee):
        manager = services.get_manager_by_subordinate_id(mock_db_session, 1)
        assert manager is None


def test_get_employee_by_staff_id(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_employee_by_staff_id` to return the mock employee
    with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
        # Act: Call the service function
        employee = services.get_employee_by_id(mock_db_session, 1)

        # Assert: Check if the correct employee is returned
        assert employee.staff_id == 1

    # Test case when employee is not found
    with patch("src.employees.crud.get_employee_by_staff_id", return_value=None):
        with pytest.raises(exceptions.EmployeeNotFoundException):
            services.get_employee_by_id(mock_db_session, 999)


def test_get_employee_by_email(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_employee_by_email` to return the mock employee
    with patch("src.employees.crud.get_employee_by_email", return_value=mock_employee):
        # Act: Call the service function
        employee = services.get_employee_by_email(mock_db_session, "test@example.com")

        # Assert: Check if the correct employee is returned
        assert employee.email == "test@example.com"

    # Test case when employee is not found
    with patch("src.employees.crud.get_employee_by_email", return_value=None):
        with pytest.raises(exceptions.EmployeeNotFoundException):
            services.get_employee_by_email(mock_db_session, "unknown@example.com")


def test_get_employees_by_manager_id(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_subordinates_by_manager_id` to return a list of employees
    with patch("src.employees.crud.get_subordinates_by_manager_id", return_value=[mock_employee]):
        # Act: Call the service function
        employees = services.get_subordinates_by_manager_id(mock_db_session, 101)

        # Assert: Check if the correct list of employees is returned
        assert len(employees) == 1
        assert employees[0].staff_id == 1

    # Test case when no employees are found
    with patch("src.employees.crud.get_subordinates_by_manager_id", return_value=[]):
        with pytest.raises(exceptions.ManagerNotFoundException):
            services.get_subordinates_by_manager_id(mock_db_session, 999)


def test_get_peers_by_staff_id_success(mock_db_session, mock_employee):
    """Test the success scenario of getting peer employees by staff_id."""

    # Arrange: Set up mock employee with a reporting manager
    mock_employee.reporting_manager = 101

    # Mock the return of get_employee_by_id to return the mock employee
    with patch("src.employees.services.get_employee_by_id", return_value=mock_employee):
        # Mock the return of get_subordinates_by_manager_id to return a list of peer employees
        mock_peer_employee = MagicMock(staff_id=2, email="peer@example.com")
        with patch(
            "src.employees.services.get_subordinates_by_manager_id",
            return_value=[mock_peer_employee],
        ):
            # Act: Call the service function
            peers = services.get_peers_by_staff_id(mock_db_session, 1)

            # Assert: Check if the correct list of peer employees is returned
            assert len(peers) == 1
            assert peers[0].staff_id == 2


def test_get_peers_by_staff_id_no_peers(mock_db_session, mock_employee):
    """Test the scenario where no peer employees are found."""

    # Arrange: Set up mock employee with a reporting manager
    mock_employee.reporting_manager = 101

    # Mock the return of get_employee_by_id to return the mock employee
    with patch("src.employees.services.get_employee_by_id", return_value=mock_employee):
        # Mock the return of get_subordinates_by_manager_id to return an empty list (no peers)
        with patch("src.employees.services.get_subordinates_by_manager_id", return_value=[]):
            # Act: Call the service function
            peers = services.get_peers_by_staff_id(mock_db_session, 1)

            # Assert: Check that the returned list is empty
            assert len(peers) == 0


def test_get_peers_by_staff_id_no_reporting_manager(mock_db_session, mock_employee):
    """Test the scenario where the employee has no reporting manager."""

    # Arrange: Set up mock employee without a reporting manager
    mock_employee.reporting_manager = None

    # Mock the return of get_employee_by_id to return the mock employee
    with patch("src.employees.services.get_employee_by_id", return_value=mock_employee):
        # Act: Call the service function
        peers = services.get_peers_by_staff_id(mock_db_session, 1)

        # Assert: Check that the returned list is empty since no reporting manager exists
        assert len(peers) == 0


def test_get_manager_by_subordinate_id_auto_approve_jack_sim(mock_db_session):
    """Test the auto-approve scenario for Jack Sim (staff_id=130002)."""

    # Act: Call the service function with Jack Sim's staff ID (130002)
    manager = services.get_manager_by_subordinate_id(mock_db_session, 130002)

    # Assert: Check that the manager is returned as None for auto-approve
    assert manager is None
