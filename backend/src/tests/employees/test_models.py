from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# pls do not delete this, this needs to be here for mock_db_session to work
# pls do not ask me why this is the case, i dont know...
from src.auth.models import Auth
from src.database import Base
from src.employees.models import DelegateLog, DelegationStatus, Employee


@pytest.fixture
def mock_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    auth_records = [
        Auth(email="manager@example.com", hashed_password="hashed_test123"),
        Auth(email="employee@example.com", hashed_password="hashed_test123"),
        Auth(email="delegate@example.com", hashed_password="hashed_test123"),
        Auth(email="test@example.com", hashed_password="hashed_test123"),
    ]
    session.add_all(auth_records)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def auth_test_data(mock_db_session):
    """Fixture to provide test auth records."""
    return {
        "manager": "manager@example.com",
        "employee": "employee@example.com",
        "delegate": "delegate@example.com",
        "test": "test@example.com",
    }


def test_create_employee(mock_db_session):
    employee = Employee(
        staff_fname="Test",
        staff_lname="User",
        dept="IT",
        position="Engineer",
        country="USA",
        email="test@example.com",
        role=2,
    )
    mock_db_session.add(employee)
    mock_db_session.commit()

    assert employee.staff_id is not None
    assert employee.staff_fname == "Test"


def test_employee_relationships(mock_db_session):
    manager = Employee(
        staff_fname="Manager",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="manager@example.com",
        role=2,
    )
    mock_db_session.add(manager)
    mock_db_session.commit()

    employee = Employee(
        staff_fname="Employee",
        staff_lname="User",
        dept="IT",
        position="Engineer",
        country="USA",
        email="employee@example.com",
        role=3,
        reporting_manager=manager.staff_id,
    )
    mock_db_session.add(employee)
    mock_db_session.commit()

    assert employee.manager.staff_fname == "Manager"
    assert employee.reporting_manager == manager.staff_id


def test_invalid_role(mock_db_session):
    with pytest.raises(Exception):
        employee = Employee(
            staff_fname="Test",
            staff_lname="User",
            dept="IT",
            position="Engineer",
            country="USA",
            email="test@example.com",
            role=4,  # Invalid role
        )
        mock_db_session.add(employee)
        mock_db_session.commit()


def test_create_delegate_log(mock_db_session):
    manager = Employee(
        staff_fname="Manager",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="manager@example.com",
        role=2,
    )
    delegate = Employee(
        staff_fname="Delegate",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="delegate@example.com",
        role=2,
    )
    mock_db_session.add_all([manager, delegate])
    mock_db_session.commit()

    delegate_log = DelegateLog(
        manager_id=manager.staff_id,
        delegate_manager_id=delegate.staff_id,
        date_of_delegation=datetime.now(),
        status_of_delegation=DelegationStatus.pending,
        description="Test delegation",
    )
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    assert delegate_log.id is not None
    assert delegate_log.status_of_delegation == DelegationStatus.pending


def test_delegate_status_change(mock_db_session):
    manager = Employee(
        staff_fname="Manager",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="manager@example.com",
        role=2,
    )
    delegate = Employee(
        staff_fname="Delegate",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="delegate@example.com",
        role=2,
    )
    mock_db_session.add_all([manager, delegate])
    mock_db_session.commit()

    delegate_log = DelegateLog(
        manager_id=manager.staff_id,
        delegate_manager_id=delegate.staff_id,
        date_of_delegation=datetime.now(),
        status_of_delegation=DelegationStatus.pending,
    )
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    delegate_log.status_of_delegation = DelegationStatus.accepted
    mock_db_session.commit()

    assert delegate_log.status_of_delegation == DelegationStatus.accepted


def test_delegate_log_relationships(mock_db_session):
    manager = Employee(
        staff_fname="Manager",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="manager@example.com",
        role=2,
    )
    delegate = Employee(
        staff_fname="Delegate",
        staff_lname="User",
        dept="IT",
        position="Manager",
        country="USA",
        email="delegate@example.com",
        role=2,
    )
    mock_db_session.add_all([manager, delegate])
    mock_db_session.commit()

    delegate_log = DelegateLog(
        manager_id=manager.staff_id,
        delegate_manager_id=delegate.staff_id,
        date_of_delegation=datetime.now(),
        status_of_delegation=DelegationStatus.pending,
    )
    mock_db_session.add(delegate_log)
    mock_db_session.commit()

    assert delegate_log.manager.staff_fname == "Manager"
    assert delegate_log.delegator.staff_fname == "Delegate"
