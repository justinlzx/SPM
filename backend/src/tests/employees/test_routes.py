import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.app import app
from src.employees import models, exceptions

# Create a TestClient instance
client = TestClient(app)


# Mock Employee fixture
@pytest.fixture
def mock_employee():
    return models.Employee(
        staff_id=1,
        email="test@example.com",
        reporting_manager=101,
        staff_fname="John",
        staff_lname="Doe",
        dept="Engineering",
        position="Developer",
        country="SG",
        role=1,
    )


@pytest.fixture
def mock_manager():
    return models.Employee(
        staff_id=101,
        email="manager@example.com",
        reporting_manager=102,
        staff_fname="Jane",
        staff_lname="Smith",
        dept="Engineering",
        position="Manager",
        country="SG",
        role=2,
    )


@pytest.fixture
def mock_peer_employees():
    return [
        models.Employee(
            staff_id=2,
            email="peer1@example.com",
            reporting_manager=101,
            staff_fname="Alice",
            staff_lname="Brown",
            dept="Engineering",
            position="Developer",
            country="SG",
            role=1,
        ),
        models.Employee(
            staff_id=3,
            email="peer2@example.com",
            reporting_manager=101,
            staff_fname="Bob",
            staff_lname="Johnson",
            dept="Engineering",
            position="Developer",
            country="SG",
            role=1,
        ),
    ]


# Test: Get Reporting Manager and Peer Employees
def test_get_reporting_manager_and_peer_employees(mock_employee, mock_manager, mock_peer_employees):
    with patch(
        "src.employees.services.get_manager_by_employee_staff_id", return_value=mock_manager
    ):
        with patch(
            "src.employees.services.get_employees_by_manager_id", return_value=mock_peer_employees
        ):
            response = client.get(f"/employee/manager/peermanager/{mock_employee.staff_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["manager_id"] == mock_manager.staff_id
            assert len(data["peer_employees"]) == len(mock_peer_employees)
            for peer in data["peer_employees"]:
                assert "staff_id" in peer
                assert "email" in peer


# Test: Get Reporting Manager and Peer Employees - Employee Not Found
def test_get_reporting_manager_and_peer_employees_employee_not_found():
    with patch(
        "src.employees.services.get_manager_by_employee_staff_id",
        side_effect=exceptions.EmployeeNotFound,  # No additional argument
    ):
        response = client.get("/employee/manager/peermanager/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Employee not found"


# Test: Get Employee by Staff ID
def test_get_employee_by_staff_id(mock_employee):
    with patch("src.employees.services.get_employee_by_staff_id", return_value=mock_employee):
        response = client.get(f"/employee/{mock_employee.staff_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["staff_id"] == mock_employee.staff_id
        assert data["email"] == mock_employee.email


# Test: Get Employee by Staff ID - Not Found
def test_get_employee_by_staff_id_not_found():
    with patch(
        "src.employees.services.get_employee_by_staff_id",
        side_effect=exceptions.EmployeeNotFound,  # No additional argument
    ):
        response = client.get("/employee/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Employee not found"


# Test: Get Employee by Email
def test_get_employee_by_email(mock_employee):
    with patch("src.employees.services.get_employee_by_email", return_value=mock_employee):
        response = client.get(f"/employee/email/{mock_employee.email}")
        assert response.status_code == 200
        data = response.json()
        assert data["staff_id"] == mock_employee.staff_id
        assert data["email"] == mock_employee.email


# Test: Get Employee by Email - Not Found
def test_get_employee_by_email_not_found():
    with patch(
        "src.employees.services.get_employee_by_email",
        side_effect=exceptions.EmployeeNotFound,  # No additional argument
    ):
        response = client.get("/employee/email/unknown@example.com")
        assert response.status_code == 404
        assert response.json()["detail"] == "Employee not found"


# Test: Get Employees Under Manager
def test_get_employees_under_manager(mock_peer_employees):
    manager_id = 101
    with patch(
        "src.employees.services.get_employees_by_manager_id", return_value=mock_peer_employees
    ):
        response = client.get(f"/employee/manager/employees/{manager_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(mock_peer_employees)
        for employee in data:
            assert "staff_id" in employee
            assert "email" in employee


# Test: Get Employees Under Manager - Not Found
def test_get_employees_under_manager_not_found():
    with patch(
        "src.employees.services.get_employees_by_manager_id",
        side_effect=exceptions.ManagerNotFound,  # No additional argument
    ):
        response = client.get("/employee/manager/employees/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Manager not found"
