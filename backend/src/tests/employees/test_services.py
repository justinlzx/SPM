import pytest
from unittest.mock import patch, MagicMock
from src.employees import services, models, exceptions
from src.tests.test_utils import mock_db_session


# Mock Employee fixture
@pytest.fixture
def mock_employee():
    return models.Employee(staff_id=1, email="test@example.com", reporting_manager=101)


def test_get_manager_by_employee_staff_id(mock_db_session, mock_employee):
    # Arrange: Mock the employee's manager
    mock_employee.manager = MagicMock(staff_id=101)

    # Patch the `get_employee_by_staff_id` function
    with patch("src.employees.services.get_employee_by_staff_id", return_value=mock_employee):
        # Act: Call the service function
        manager = services.get_manager_by_employee_staff_id(mock_db_session, 1)

        # Assert: Check if the correct manager is returned
        assert manager.staff_id == 101

    # Test case when employee reports to themselves (manager is None)
    mock_employee.manager = mock_employee  # Employee reports to themselves

    with patch("src.employees.services.get_employee_by_staff_id", return_value=mock_employee):
        manager = services.get_manager_by_employee_staff_id(mock_db_session, 1)
        assert manager is None


def test_get_employee_by_staff_id(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_employee_by_staff_id` to return the mock employee
    with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
        # Act: Call the service function
        employee = services.get_employee_by_staff_id(mock_db_session, 1)

        # Assert: Check if the correct employee is returned
        assert employee.staff_id == 1

    # Test case when employee is not found
    with patch("src.employees.crud.get_employee_by_staff_id", return_value=None):
        with pytest.raises(exceptions.EmployeeNotFound):
            services.get_employee_by_staff_id(mock_db_session, 999)


def test_get_employee_by_email(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_employee_by_email` to return the mock employee
    with patch("src.employees.crud.get_employee_by_email", return_value=mock_employee):
        # Act: Call the service function
        employee = services.get_employee_by_email(mock_db_session, "test@example.com")

        # Assert: Check if the correct employee is returned
        assert employee.email == "test@example.com"

    # Test case when employee is not found
    with patch("src.employees.crud.get_employee_by_email", return_value=None):
        with pytest.raises(exceptions.EmployeeNotFound):
            services.get_employee_by_email(mock_db_session, "unknown@example.com")


def test_get_employees_by_manager_id(mock_db_session, mock_employee):
    # Arrange: Patch the `crud.get_employees_by_manager_id` to return a list of employees
    with patch("src.employees.crud.get_employees_by_manager_id", return_value=[mock_employee]):
        # Act: Call the service function
        employees = services.get_employees_by_manager_id(mock_db_session, 101)

        # Assert: Check if the correct list of employees is returned
        assert len(employees) == 1
        assert employees[0].staff_id == 1

    # Test case when no employees are found
    with patch("src.employees.crud.get_employees_by_manager_id", return_value=[]):
        with pytest.raises(exceptions.ManagerNotFound):
            services.get_employees_by_manager_id(mock_db_session, 999)
