import pytest
from src.employees.exceptions import (
    EmployeeNotFoundException,
    ManagerWithIDNotFoundException,
    ManagerNotFoundException,
)


def test_employee_not_found_exception():
    with pytest.raises(EmployeeNotFoundException) as excinfo:
        raise EmployeeNotFoundException()
    assert str(excinfo.value) == "Employee not found"


def test_manager_with_id_not_found_exception():
    manager_id = 101
    with pytest.raises(ManagerWithIDNotFoundException) as excinfo:
        raise ManagerWithIDNotFoundException(manager_id)
    assert str(excinfo.value) == f"Manager with ID {manager_id} not found"
    assert excinfo.value.manager_id == manager_id


def test_manager_not_found_exception():
    with pytest.raises(ManagerNotFoundException) as excinfo:
        raise ManagerNotFoundException()
    assert str(excinfo.value) == "Manager not found"
