from unittest.mock import patch
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
    get_all_received_delegations,
    get_all_sent_delegations,
    get_delegation_log_by_delegate,
    get_delegation_log_by_manager,
    get_employee_by_email,
    get_employee_by_staff_id,
    get_employee_full_name,
    get_existing_delegation,
    create_delegation,
    get_manager_of_employee,
    get_peer_employees,
    get_pending_approval_delegations,
    get_sent_delegations,
    get_subordinates_by_manager_id,
    is_employee_locked_in_delegation,
    mark_delegation_as_undelegated,
    remove_delegate_from_arrangements,
    update_delegation_status,
    update_pending_arrangements_for_delegate,
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
        reporting_manager=1,
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
        reporting_manager=1,
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


def test_get_employee_by_staff_id_exists(test_db, seed_data):
    # Test when the staff ID exists
    result = get_employee_by_staff_id(test_db, staff_id=1)
    assert result is not None
    assert result.staff_id == 1


def test_get_employee_by_staff_id_not_exists(test_db):
    # Test when the staff ID does not exist
    result = get_employee_by_staff_id(test_db, staff_id=999)
    assert result is None


def test_get_employee_by_email_exists(test_db, seed_data):
    # Test retrieval of an employee by email
    result = get_employee_by_email(test_db, email="john.doe@example.com")
    assert result is not None
    assert result.email == "john.doe@example.com"


def test_get_employee_by_email_not_exists(test_db):
    # Test with an email that doesn’t exist
    result = get_employee_by_email(test_db, email="nonexistent@example.com")
    assert result is None


def test_get_subordinates_by_manager_id_has_subordinates(test_db, seed_data):
    # Test for retrieving a list of employees with a specific manager_id
    result = get_subordinates_by_manager_id(test_db, manager_id=1)
    assert isinstance(result, list)
    assert len(result) > 0, "Expected at least one subordinate"


def test_get_subordinates_by_manager_id_no_subordinates(test_db):
    # Test when no subordinates are available for a manager_id
    result = get_subordinates_by_manager_id(test_db, manager_id=999)
    assert result == []


def test_update_delegation_status_no_description_overwrite(test_db, seed_data):
    # Update without a description should not overwrite if description exists
    delegation = test_db.query(DelegateLog).filter_by(manager_id=1, delegate_manager_id=2).first()
    delegation.description = "Initial description"
    updated_delegation = update_delegation_status(test_db, delegation, DelegationStatus.accepted)
    assert updated_delegation.description == "Initial description"


def test_get_delegation_log_by_delegate_multiple_logs(test_db, seed_data):
    # Insert additional logs for the same delegate_manager_id
    delegation1 = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    delegation2 = DelegateLog(
        manager_id=3, delegate_manager_id=2, status_of_delegation=DelegationStatus.accepted
    )
    test_db.add_all([delegation1, delegation2])
    test_db.commit()

    result = get_delegation_log_by_delegate(test_db, staff_id=2)
    assert result is not None
    assert result.manager_id == 1  # Check if it returns the first log for delegate_manager_id=2


def test_create_delegation_new_entry(test_db):
    # Attempt to create a new delegation for IDs not in seed_data
    new_delegation = create_delegation(test_db, staff_id=10, delegate_manager_id=20)
    assert new_delegation is not None
    assert new_delegation.manager_id == 10
    assert new_delegation.delegate_manager_id == 20
    assert new_delegation.status_of_delegation == DelegationStatus.pending


def test_update_pending_arrangements_for_delegate_no_match(test_db, seed_data):
    # Call with manager/delegate IDs with no pending arrangements
    update_pending_arrangements_for_delegate(test_db, manager_id=99, delegate_manager_id=100)
    # Verify no records updated by querying arrangements table
    result = test_db.query(LatestArrangement).filter_by(approving_officer=100).all()
    assert len(result) == 0, "Expected no arrangements to be updated"


def test_update_delegation_status_to_undelegated(test_db, seed_data):
    delegation = test_db.query(DelegateLog).filter_by(manager_id=1, delegate_manager_id=2).first()
    updated_delegation = update_delegation_status(test_db, delegation, DelegationStatus.undelegated)
    assert updated_delegation.status_of_delegation == DelegationStatus.undelegated


def test_get_existing_delegation_excludes_non_pending_accepted(test_db, seed_data):
    # Insert a delegation with 'rejected' status
    delegation = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.rejected
    )
    test_db.add(delegation)
    test_db.commit()

    result = get_existing_delegation(test_db, staff_id=1, delegate_manager_id=2)
    assert result is not None
    assert result.status_of_delegation != DelegationStatus.rejected  # Ensure it excludes 'rejected'


def test_get_delegation_log_by_delegate_non_existent(test_db):
    result = get_delegation_log_by_delegate(test_db, staff_id=12345)  # ID not in seed data
    assert result is None, "Expected no logs to be found for a non-existent delegate ID"


def test_create_delegation_with_maximum_values(test_db):
    # Assuming IDs or text length limits, adjust as necessary
    max_staff_id = 2**31 - 1
    max_delegate_manager_id = 2**31 - 2

    new_delegation = create_delegation(
        test_db, staff_id=max_staff_id, delegate_manager_id=max_delegate_manager_id
    )
    assert new_delegation is not None
    assert new_delegation.manager_id == max_staff_id
    assert new_delegation.delegate_manager_id == max_delegate_manager_id


def test_update_pending_arrangements_for_delegate_with_pending_arrangements(test_db, seed_data):
    # Arrange: Add a pending arrangement with a specific manager_id
    arrangement = LatestArrangement(
        update_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        requester_staff_id=3,
        wfh_date="2023-10-26",
        wfh_type="full",
        current_approval_status="pending approval",
        approving_officer=1,  # Original manager
        reason_description="WFH arrangement due to personal reasons",
    )
    test_db.add(arrangement)
    test_db.commit()

    # Act: Update pending arrangements for delegate
    update_pending_arrangements_for_delegate(test_db, manager_id=1, delegate_manager_id=2)

    # Assert: Check if the arrangement was updated to use the delegate manager
    updated_arrangement = test_db.query(LatestArrangement).filter_by(requester_staff_id=3).first()
    assert updated_arrangement.delegate_approving_officer == 2


def test_get_delegation_log_by_manager_found(test_db, seed_data):
    # Act: Call function with existing manager_id
    result = get_delegation_log_by_manager(test_db, staff_id=1)

    # Assert: Check that result is not None and matches expected values
    assert result is not None
    assert result.manager_id == 1


def test_remove_delegate_from_arrangements(test_db, seed_data):
    # Arrange: Add an arrangement with a delegate assigned
    arrangement = LatestArrangement(
        update_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        requester_staff_id=4,
        wfh_date="2023-10-26",
        wfh_type="full",  # Use a valid value according to the CHECK constraint
        current_approval_status="pending approval",
        delegate_approving_officer=2,
        reason_description="WFH arrangement for full day",
    )
    test_db.add(arrangement)
    test_db.commit()

    # Act: Remove delegate from arrangements
    remove_delegate_from_arrangements(test_db, delegate_manager_id=2)

    # Assert: Ensure delegate_approving_officer is set to None
    updated_arrangement = test_db.query(LatestArrangement).filter_by(requester_staff_id=4).first()
    assert updated_arrangement.delegate_approving_officer is None


def test_mark_delegation_as_undelegated(test_db, seed_data):
    # Arrange: Use an existing delegation log
    delegation_log = (
        test_db.query(DelegateLog).filter_by(manager_id=1, delegate_manager_id=2).first()
    )

    # Act: Mark delegation as undelegated
    updated_log = mark_delegation_as_undelegated(test_db, delegation_log)

    # Assert: Verify that status is updated to 'undelegated'
    assert updated_log.status_of_delegation == DelegationStatus.undelegated


def test_get_sent_delegations(test_db, seed_data):
    # Act: Retrieve sent delegations for manager
    result = get_sent_delegations(test_db, staff_id=1)

    # Assert: Ensure result is not None and contains expected values
    assert result is not None
    assert result[0].manager_id == 1


def test_get_employee_full_name_exists(test_db, seed_data):
    # Act: Retrieve full name for existing employee
    result = get_employee_full_name(test_db, staff_id=1)

    # Assert: Check full name is correct
    assert result == "John Doe"


def test_get_employee_by_email_edge_cases(test_db):
    # Test with None email
    result = get_employee_by_email(test_db, None)
    assert result is None

    # Test with empty string
    result = get_employee_by_email(test_db, "")
    assert result is None


def test_update_delegation_status_none_delegation(test_db):
    with pytest.raises(AttributeError):
        update_delegation_status(test_db, None, DelegationStatus.accepted)


def test_update_pending_arrangements_for_delegate_empty_db(test_db):
    # Test with empty database
    update_pending_arrangements_for_delegate(test_db, 1, 2)
    assert test_db.query(LatestArrangement).count() == 0


def test_update_pending_arrangements_for_delegate_non_pending(test_db, seed_data):
    # Add arrangement that's not pending
    arrangement = LatestArrangement(
        update_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        requester_staff_id=5,
        wfh_date="2023-10-26",
        wfh_type="full",
        current_approval_status="approved",
        approving_officer=1,
        reason_description="Approved WFH",
    )
    test_db.add(arrangement)
    test_db.commit()

    # Should not update non-pending arrangements
    update_pending_arrangements_for_delegate(test_db, 1, 2)
    updated = test_db.query(LatestArrangement).filter_by(requester_staff_id=5).first()
    assert updated.delegate_approving_officer is None


def test_remove_delegate_from_arrangements_non_pending(test_db, seed_data):
    # Add arrangement with non-pending status
    arrangement = LatestArrangement(
        update_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        requester_staff_id=6,
        wfh_date="2023-10-26",
        wfh_type="full",
        current_approval_status="approved",
        delegate_approving_officer=2,
        reason_description="Approved WFH",
    )
    test_db.add(arrangement)
    test_db.commit()

    # Should not remove delegate from non-pending arrangements
    remove_delegate_from_arrangements(test_db, 2)
    updated = test_db.query(LatestArrangement).filter_by(requester_staff_id=6).first()
    assert updated.delegate_approving_officer == 2


def test_get_delegation_log_by_manager_multiple_statuses(test_db, seed_data):
    # Add multiple delegations with different statuses
    delegations = [
        DelegateLog(manager_id=1, delegate_manager_id=3, status_of_delegation=status)
        for status in DelegationStatus
    ]
    test_db.add_all(delegations)
    test_db.commit()

    # Should return first delegation regardless of status
    result = get_delegation_log_by_manager(test_db, 1)
    assert result is not None
    assert result.manager_id == 1


def test_get_employee_full_name_special_chars(test_db):
    # Test handling of special characters in names
    employee = Employee(
        staff_id=100,
        staff_fname="O'Connor",
        staff_lname="Smith-Jones",
        email="test@example.com",
        dept="IT",
        position="Developer",
        country="SG",
        role=1,
    )
    test_db.add(employee)
    test_db.commit()

    result = get_employee_full_name(test_db, 100)
    assert result == "O'Connor Smith-Jones"


def test_get_pending_approval_delegations(test_db, seed_data):
    # Test retrieving pending delegations for a delegate manager
    result = get_pending_approval_delegations(test_db, staff_id=2)
    assert result is not None
    assert len(result) > 0
    assert all(d.delegate_manager_id == 2 for d in result)
    assert all(
        d.status_of_delegation in [DelegationStatus.pending, DelegationStatus.accepted]
        for d in result
    )


def test_get_pending_approval_delegations_none(test_db):
    # Test when no pending delegations exist
    result = get_pending_approval_delegations(test_db, staff_id=999)
    assert result == []


def test_get_employee_full_name_missing_components(test_db):
    # Test with minimal required fields
    emp1 = Employee(
        staff_id=101,
        staff_fname="John",
        staff_lname="",  # Empty string instead of None
        dept="IT",
        position="Developer",
        country="SG",
        email="john@example.com",
        role=1,
        reporting_manager=1,  # Add if required
    )
    emp2 = Employee(
        staff_id=102,
        staff_fname="",  # Empty string instead of None
        staff_lname="Doe",
        dept="IT",
        position="Developer",
        country="SG",
        email="doe@example.com",
        role=1,
        reporting_manager=1,  # Add if required
    )
    test_db.add_all([emp1, emp2])
    test_db.commit()

    assert get_employee_full_name(test_db, 101) == "John "
    assert get_employee_full_name(test_db, 102) == " Doe"


def test_get_all_sent_delegations(test_db, seed_data):
    # Test retrieving all sent delegations for a manager
    result = get_all_sent_delegations(test_db, staff_id=1)
    assert result is not None
    assert len(result) > 0
    assert all(d.manager_id == 1 for d in result)


def test_get_all_sent_delegations_none(test_db):
    # Test when no sent delegations exist
    result = get_all_sent_delegations(test_db, staff_id=999)
    assert result == []


def test_get_all_received_delegations(test_db, seed_data):
    # Test retrieving all received delegations for a delegate
    result = get_all_received_delegations(test_db, staff_id=2)
    assert result is not None
    assert len(result) > 0
    assert all(d.delegate_manager_id == 2 for d in result)


def test_get_all_received_delegations_none(test_db):
    # Test when no received delegations exist
    result = get_all_received_delegations(test_db, staff_id=999)
    assert result == []


def test_get_manager_of_employee(test_db, seed_data):
    # Create test employees with manager relationship
    manager = Employee(
        staff_id=201,
        staff_fname="Manager",
        staff_lname="One",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager@example.com",
        role=1,
    )
    employee = Employee(
        staff_id=202,
        staff_fname="Employee",
        staff_lname="One",
        dept="IT",
        position="Developer",
        country="SG",
        email="employee@example.com",
        role=2,
        reporting_manager=201,
    )
    test_db.add_all([manager, employee])
    test_db.commit()

    # Refresh employee to load relationships
    test_db.refresh(employee)

    # Test getting manager
    result = get_manager_of_employee(test_db, employee)
    assert result is not None
    assert result.staff_id == 201


def test_get_manager_of_employee_self_reporting(test_db):
    # Test when employee reports to themselves (e.g., CEO)
    employee = Employee(
        staff_id=203,
        staff_fname="Self",
        staff_lname="Manager",
        dept="Executive",
        position="CEO",
        country="SG",
        email="ceo@example.com",
        role=1,
        reporting_manager=203,  # Reports to self
    )
    test_db.add(employee)
    test_db.commit()

    test_db.refresh(employee)
    result = get_manager_of_employee(test_db, employee)
    assert result is None


def test_get_manager_of_employee_no_manager(test_db):
    # Test when employee has no manager
    employee = Employee(
        staff_id=204,
        staff_fname="No",
        staff_lname="Manager",
        dept="IT",
        position="Developer",
        country="SG",
        email="no.manager@example.com",
        role=2,
        reporting_manager=None,
    )
    test_db.add(employee)
    test_db.commit()

    test_db.refresh(employee)
    result = get_manager_of_employee(test_db, employee)
    assert result is None


def test_get_peer_employees(test_db):
    # Create a manager and multiple peer employees
    manager = Employee(
        staff_id=301,
        staff_fname="Manager",
        staff_lname="Team",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager.team@example.com",
        role=1,
    )
    peers = [
        Employee(
            staff_id=302 + i,
            staff_fname=f"Peer{i}",
            staff_lname="Employee",
            dept="IT",
            position="Developer",
            country="SG",
            email=f"peer{i}@example.com",
            role=2,
            reporting_manager=301,
        )
        for i in range(3)
    ]
    test_db.add(manager)
    test_db.add_all(peers)
    test_db.commit()

    # Test getting peer employees
    result = get_peer_employees(test_db, manager_id=301)
    assert len(result) == 3
    assert all(emp.reporting_manager == 301 for emp in result)


def test_get_peer_employees_no_peers(test_db):
    # Test when manager has no peer employees
    result = get_peer_employees(test_db, manager_id=999)
    assert result == []


def test_is_employee_locked_in_delegation(test_db, seed_data):
    # Test when employee is locked in delegation (as manager)
    result = is_employee_locked_in_delegation(test_db, employee_id=1)
    assert result is True

    # Test when employee is locked in delegation (as delegate)
    result = is_employee_locked_in_delegation(test_db, employee_id=2)
    assert result is True


def test_is_employee_locked_in_delegation_not_locked(test_db):
    # Test when employee is not locked in any delegation
    result = is_employee_locked_in_delegation(test_db, employee_id=999)
    assert result is False


def test_is_employee_locked_in_delegation_completed_status(test_db, seed_data):
    # Create new employees
    employee3 = Employee(
        staff_id=3,
        staff_fname="Test",
        staff_lname="User",
        dept="IT",
        position="Developer",
        country="SG",
        email="test3@example.com",
        role=1,
        reporting_manager=1,
    )
    employee4 = Employee(
        staff_id=4,
        staff_fname="Test",
        staff_lname="User",
        dept="IT",
        position="Developer",
        country="SG",
        email="test4@example.com",
        role=1,
        reporting_manager=1,
    )
    test_db.add_all([employee3, employee4])
    test_db.commit()

    # Add only undelegated status delegation
    delegation = DelegateLog(
        manager_id=3,
        delegate_manager_id=4,
        status_of_delegation=DelegationStatus.undelegated,
        date_of_delegation=datetime.utcnow(),
    )
    test_db.add(delegation)
    test_db.commit()

    # Verify employees are not locked in delegation
    result_manager = is_employee_locked_in_delegation(test_db, employee_id=3)
    result_delegate = is_employee_locked_in_delegation(test_db, employee_id=4)

    assert result_manager is False  # Should not be locked since status is undelegated
    assert result_delegate is False  # Should not be locked since status is undelegated

    # Add a pending delegation to verify the function works correctly
    pending_delegation = DelegateLog(
        manager_id=3,
        delegate_manager_id=4,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.utcnow(),
    )
    test_db.add(pending_delegation)
    test_db.commit()

    # Now they should be locked
    result_manager_pending = is_employee_locked_in_delegation(test_db, employee_id=3)
    result_delegate_pending = is_employee_locked_in_delegation(test_db, employee_id=4)

    assert result_manager_pending is True  # Should be locked with pending status
    assert result_delegate_pending is True  # Should be locked with pending status


def test_get_employee_full_name_complete(test_db):
    # Test with a complete employee record
    employee = Employee(
        staff_id=101,
        staff_fname="John",
        staff_lname="Doe",
        dept="IT",
        position="Developer",
        country="SG",
        email="john.doe@example.com",
        role=1,
        reporting_manager=1,
    )
    test_db.add(employee)
    test_db.commit()

    result = get_employee_full_name(test_db, staff_id=101)
    assert result == "John Doe"


def test_get_employee_full_name_not_found(test_db):
    # Test with non-existent staff_id
    result = get_employee_full_name(test_db, staff_id=999)
    assert result == "Unknown"


def test_get_employee_full_name_with_spaces(test_db):
    # Test with names containing spaces
    employee = Employee(
        staff_id=102,
        staff_fname="Mary Jane",
        staff_lname="Smith Wilson",
        dept="IT",
        position="Developer",
        country="SG",
        email="mary.jane@example.com",
        role=1,
        reporting_manager=1,
    )
    test_db.add(employee)
    test_db.commit()

    result = get_employee_full_name(test_db, staff_id=102)
    assert result == "Mary Jane Smith Wilson"


def test_get_employee_full_name_with_special_chars(test_db):
    # Test with names containing special characters
    employee = Employee(
        staff_id=103,
        staff_fname="José-María",
        staff_lname="O'Connor",
        dept="IT",
        position="Developer",
        country="SG",
        email="jose.maria@example.com",
        role=1,
        reporting_manager=1,
    )
    test_db.add(employee)
    test_db.commit()

    result = get_employee_full_name(test_db, staff_id=103)
    assert result == "José-María O'Connor"


def test_get_employee_full_name_all_branches(test_db):
    # Test Case 1: When employee exists
    employee = Employee(
        staff_id=5,
        staff_fname="John",
        staff_lname="Doe",
        dept="IT",
        position="Developer",
        country="SG",
        email="john.doe@example.com",
        role=1,
        reporting_manager=1,
    )
    test_db.add(employee)
    test_db.commit()

    # Test the if branch - when employee is found
    result = get_employee_full_name(test_db, staff_id=5)
    assert result == "John Doe"

    # Test Case 2: When employee doesn't exist
    # Test the else branch - when employee is None
    result = get_employee_full_name(test_db, staff_id=999)
    assert result == "Unknown"

    # Test Case 3: Clear the database to ensure both branches are covered
    test_db.query(Employee).delete()
    test_db.commit()
    result = get_employee_full_name(test_db, staff_id=5)
    assert result == "Unknown"
