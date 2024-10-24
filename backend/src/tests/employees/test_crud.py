import pytest
from sqlalchemy.sql import elements
from src.employees import crud, models


@pytest.fixture
def mock_employee():
    return models.Employee(staff_id=1, email="test@example.com", reporting_manager=101)


def compare_binary_expressions(
    actual: elements.BinaryExpression, expected: elements.BinaryExpression
):
    assert str(actual) == str(expected), f"Expected {expected}, but got {actual}"


def test_get_employee_by_staff_id(mock_db_session, mock_employee):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_employee

    result = crud.get_employee_by_staff_id(mock_db_session, 1)

    assert result == mock_employee
    mock_db_session.query.assert_called_once()
    filter_args = mock_db_session.query.return_value.filter.call_args[0][0]
    compare_binary_expressions(filter_args, models.Employee.staff_id == 1)


def test_get_employee_by_email(mock_db_session, mock_employee):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_employee

    result = crud.get_employee_by_email(mock_db_session, "test@example.com")

    assert result == mock_employee
    mock_db_session.query.assert_called_once()
    filter_args = mock_db_session.query.return_value.filter.call_args[0][0]
    compare_binary_expressions(
        filter_args, crud.func.lower(models.Employee.email) == "test@example.com"
    )


def test_get_subordinates_by_manager_id(mock_db_session, mock_employee):
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_employee]

    result = crud.get_subordinates_by_manager_id(mock_db_session, 101)

    assert result == [mock_employee]
    mock_db_session.query.assert_called_once()
    filter_args = mock_db_session.query.return_value.filter.call_args[0][0]
    compare_binary_expressions(filter_args, models.Employee.reporting_manager == 101)
