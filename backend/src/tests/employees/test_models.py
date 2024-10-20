from datetime import datetime
from unittest.mock import MagicMock

import pytest
from src.employees.models import DelegateLog, DelegationStatus, Employee
from src.tests.test_utils import mock_db_session


def test_create_employee(mock_db_session):
    # Create a mock Auth entry
    mock_auth_entry = MagicMock()
    mock_auth_entry.email = "jane.doe@test.com"

    # Create a mock Employee entry
    employee = Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Doe",
        email="jane.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=None,
    )

    # Add the mock employee to the session and commit the transaction
    mock_db_session.add(employee)
    mock_db_session.commit()  # Ensure commit is called
    mock_db_session.commit.assert_called_once()


def test_employee_relationships(mock_db_session):
    # Create mock Auth entries
    mock_auth_entry_director = MagicMock()
    mock_auth_entry_director.email = "john.smith@test.com"

    mock_auth_entry_manager = MagicMock()
    mock_auth_entry_manager.email = "jane.doe@test.com"

    # Create mock Employee entries
    director = Employee(
        staff_id=2,
        staff_fname="John",
        staff_lname="Smith",
        email="john.smith@test.com",
        dept="IT",
        position="Director",
        country="USA",
        role=1,
    )

    manager = Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Doe",
        email="jane.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=2,
    )

    # Add mock employees to the session and commit the transaction
    mock_db_session.add(director)
    mock_db_session.add(manager)
    mock_db_session.commit()  # Ensure commit is called
    mock_db_session.commit.assert_called_once()

    # Check the relationship between manager and director
    assert manager.reporting_manager == director.staff_id


def test_invalid_role(mock_db_session):
    # Create a mock Employee entry with an invalid role
    invalid_employee = Employee(
        staff_id=3,
        staff_fname="Invalid",
        staff_lname="User",
        email="invalid.user@test.com",
        dept="HR",
        position="Analyst",
        country="USA",
        role=4,  # Invalid role, should be 1, 2, or 3
        reporting_manager=None,
    )

    # Simulate manual role validation for the purpose of this test
    def mock_commit():
        if invalid_employee.role not in [1, 2, 3]:
            raise ValueError("Invalid role. Role must be 1, 2, or 3.")
        mock_db_session._real_commit()  # Call the real commit method

    # Patch the commit method to add custom validation
    mock_db_session._real_commit = mock_db_session.commit
    mock_db_session.commit = mock_commit

    # Add the mock employee and expect the validation to raise an exception
    mock_db_session.add(invalid_employee)
    with pytest.raises(ValueError, match="Invalid role"):
        mock_db_session.commit()

    # Verify commit was not called
    mock_db_session._real_commit.assert_not_called()


def test_create_delegate_log(mock_db_session):
    # Create mock employees
    manager = Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Doe",
        email="jane.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=None,
    )

    delegate_manager = Employee(
        staff_id=2,
        staff_fname="John",
        staff_lname="Smith",
        email="john.smith@test.com",
        dept="IT",
        position="Director",
        country="USA",
        role=2,
        reporting_manager=None,
    )

    # Create a DelegateLog entry
    delegate_log = DelegateLog(
        manager_id=1,
        delegate_manager_id=2,
        status_of_delegation=DelegationStatus.pending,
        description="Delegation for leave approval",
        date_of_delegation=datetime.utcnow(),
    )

    # Configure mock behavior to simulate adding and committing employees and logs
    mock_db_session.add(manager)
    mock_db_session.add(delegate_manager)
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    # Set up mock return values for query().get()
    mock_db_session.query().get.return_value = delegate_log

    # Expunge the object to simulate real-world behavior
    mock_db_session.expunge(delegate_log)

    # Re-query the delegate log object using mock
    retrieved_delegate_log = mock_db_session.query(DelegateLog).get(delegate_log.id)

    # Check if the relationships are set correctly
    assert retrieved_delegate_log.manager_id == manager.staff_id
    assert retrieved_delegate_log.delegate_manager_id == delegate_manager.staff_id


def test_delegate_status_change(mock_db_session):
    # Create a mock delegate log with initial pending status
    delegate_log = DelegateLog(
        manager_id=1,
        delegate_manager_id=2,
        status_of_delegation=DelegationStatus.pending,
        description="Delegation for project management",
        date_of_delegation=datetime.utcnow(),
    )

    # Add the delegate log to the session
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    # Ensure initial status is pending
    assert delegate_log.status_of_delegation == DelegationStatus.pending

    # Change status to accepted
    delegate_log.status_of_delegation = DelegationStatus.accepted
    mock_db_session.commit()

    # Check that the status changed correctly
    assert delegate_log.status_of_delegation == DelegationStatus.accepted

    # Change status to rejected
    delegate_log.status_of_delegation = DelegationStatus.rejected
    mock_db_session.commit()

    # Check that the status changed to rejected
    assert delegate_log.status_of_delegation == DelegationStatus.rejected


def test_delegate_log_relationships(mock_db_session):
    # Create mock employees
    manager = Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Doe",
        email="jane.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=None,
    )

    delegate_manager = Employee(
        staff_id=2,
        staff_fname="John",
        staff_lname="Smith",
        email="john.smith@test.com",
        dept="IT",
        position="Director",
        country="USA",
        role=2,
        reporting_manager=None,
    )

    # Create a DelegateLog entry
    delegate_log = DelegateLog(
        manager_id=1,
        delegate_manager_id=2,
        status_of_delegation=DelegationStatus.pending,
        description="Delegation for temporary coverage",
        date_of_delegation=datetime.utcnow(),
    )

    # Configure mock behavior to simulate adding and committing employees and logs
    mock_db_session.add(manager)
    mock_db_session.add(delegate_manager)
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    # Set up mock return values for query().filter_by().first()
    mock_db_session.query().filter_by().first.return_value = delegate_log

    # Query the session to retrieve the latest delegate log using mock
    reloaded_delegate_log = mock_db_session.query(DelegateLog).filter_by(manager_id=1).first()

    # Check relationships
    assert reloaded_delegate_log.manager_id == manager.staff_id
    assert reloaded_delegate_log.delegate_manager_id == delegate_manager.staff_id
    assert reloaded_delegate_log.status_of_delegation == DelegationStatus.pending
