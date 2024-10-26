from sqlalchemy.exc import IntegrityError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.employees.models import (
    Base,
    DelegateLog,
    DelegationStatus,
    DelegateLog,
    DelegationStatus,
    Employee,
)
from src.arrangements.models import LatestArrangement
from src.auth.models import Auth
from src.employees.crud import (
    get_delegation_log_by_delegate,
    get_employee_full_name,
    get_existing_delegation,
    create_delegation,
    update_delegation_status,
)
from datetime import datetime

# Configure the in-memory SQLite database
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)  # Automatically use this for each test
def test_db():
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.rollback()  # Reset the session after each test
    Base.metadata.drop_all(bind=engine)  # Clear tables
    db.close()


@pytest.fixture
def seed_data(test_db):
    # Insert sample data into Auth, Employee, DelegateLog, and LatestArrangement tables
    auth_record = Auth(email="john.doe@example.com", hashed_password="hashed_password_example")

    employee1 = Employee(
        staff_id=1,
        staff_fname="John",
        staff_lname="Doe",
        dept="IT",
        position="Manager",
        country="SG",
        email="john.doe@example.com",
        role=1,
    )
    employee2 = Employee(
        staff_id=2,
        staff_fname="Jane",
        staff_lname="Smith",
        dept="HR",
        position="Manager",
        country="SG",
        email="jane.smith@example.com",
        role=1,
    )

    # Add delegations with different statuses
    delegation1 = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    delegation2 = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.accepted
    )

    # Insert into LatestArrangement with update_datetime populated
    arrangement = LatestArrangement(
        update_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),  # Set current timestamp
        requester_staff_id=1,
        wfh_date="2023-10-25",
        wfh_type="full",
        current_approval_status="pending approval",
        approving_officer=2,
        reason_description="WFH arrangement",
    )

    test_db.merge(auth_record)  # Use merge instead of add for Auth
    test_db.merge(employee1)
    test_db.merge(employee2)
    test_db.add_all([delegation1, delegation2, arrangement])  # add is fine for new records
    test_db.commit()


def test_get_existing_delegation_found(test_db, seed_data):
    # Test retrieval of a delegation record based on manager and delegate
    result = get_existing_delegation(test_db, staff_id=1, delegate_manager_id=2)
    assert result is not None
    assert result.delegate_manager_id == 2
    assert result.status_of_delegation in [DelegationStatus.pending, DelegationStatus.accepted]


def test_get_existing_delegation_not_found(test_db, seed_data):
    # Use IDs that do not exist in seed_data to ensure no matching delegation is found
    result = get_existing_delegation(test_db, staff_id=99, delegate_manager_id=100)
    assert result is None


def test_create_delegation(test_db):
    # Test creation of a new delegation record
    new_delegation = create_delegation(test_db, staff_id=1, delegate_manager_id=2)
    assert new_delegation is not None
    assert new_delegation.manager_id == 1
    assert new_delegation.delegate_manager_id == 2
    assert new_delegation.status_of_delegation == DelegationStatus.pending


def test_get_existing_delegation_different_status(test_db, seed_data):
    # Ensure it does not retrieve delegations with statuses other than pending or accepted
    new_delegation = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.rejected
    )
    test_db.add(new_delegation)
    test_db.commit()

    result = get_existing_delegation(test_db, staff_id=1, delegate_manager_id=2)
    assert result.status_of_delegation in [DelegationStatus.pending, DelegationStatus.accepted]


def test_get_existing_delegation_multiple_matches(test_db, seed_data):
    # Insert multiple pending/accepted delegations and check if the first one is returned
    delegation3 = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    test_db.add(delegation3)
    test_db.commit()

    result = get_existing_delegation(test_db, staff_id=1, delegate_manager_id=2)
    assert result.status_of_delegation == DelegationStatus.pending


def test_create_delegation_duplicate(test_db, seed_data):
    # Attempt to create a duplicate delegation
    original_delegation = create_delegation(test_db, staff_id=1, delegate_manager_id=2)
    duplicate_delegation = create_delegation(test_db, staff_id=1, delegate_manager_id=2)

    assert original_delegation.id == duplicate_delegation.id  # Ensure duplicate is not created


def test_create_delegation_invalid_ids(test_db):
    # Attempt creation with invalid staff_id or delegate_manager_id
    with pytest.raises(IntegrityError):  # Replace with the actual exception raised
        create_delegation(test_db, staff_id=-1, delegate_manager_id=9999)


def test_get_delegation_log_by_delegate_no_match(test_db):
    result = get_delegation_log_by_delegate(test_db, staff_id=999)
    assert result is None


def test_get_delegation_log_by_delegate_multiple(test_db, seed_data):
    # Add another delegation to the same delegate manager
    delegation = DelegateLog(
        manager_id=3, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    test_db.add(delegation)
    test_db.commit()

    result = get_delegation_log_by_delegate(test_db, staff_id=2)
    assert result.delegate_manager_id == 2
    assert result.manager_id == 1  # Returns first match by default


def test_update_delegation_status_with_description(test_db, seed_data):
    # Update a delegation's status and add a description
    delegation = test_db.query(DelegateLog).filter_by(manager_id=1, delegate_manager_id=2).first()
    updated_delegation = update_delegation_status(
        test_db, delegation, DelegationStatus.accepted, "Test description"
    )

    assert updated_delegation.status_of_delegation == DelegationStatus.accepted
    assert updated_delegation.description == "Test description"


def test_update_delegation_status_without_description(test_db, seed_data):
    delegation = test_db.query(DelegateLog).filter_by(manager_id=1, delegate_manager_id=2).first()
    updated_delegation = update_delegation_status(test_db, delegation, DelegationStatus.rejected)

    assert updated_delegation.status_of_delegation == DelegationStatus.rejected
    assert updated_delegation.description is None


def test_get_employee_full_name_not_found(test_db):
    result = get_employee_full_name(test_db, staff_id=999)
    assert result == "Unknown"


def test_get_employee_full_name_found(test_db, seed_data):
    result = get_employee_full_name(test_db, staff_id=1)
    assert result == "John Doe"
