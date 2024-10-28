from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.models import Auth
from src.employees.exceptions import EmployeeNotFoundException
from src.employees.models import Base, DelegateLog, DelegationStatus, Employee
from src.employees.services import (
    DelegationApprovalStatus,
    delegate_manager,
    get_employee_by_id,
    get_manager_by_subordinate_id,
    get_peers_by_staff_id,
    process_delegation_status,
    undelegate_manager,
    view_all_delegations,
    view_delegations,
)

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


# @pytest.fixture
# def seed_data(test_db):
#     # Create auth and employee records
#     auth_record = Auth(email="john.doe@example.com", hashed_password="hashed_password_example")
#     employees = [
#         Employee(
#             staff_id=1,
#             staff_fname="John",
#             staff_lname="Doe",
#             dept="IT",
#             position="Manager",
#             country="SG",
#             email="john.doe@example.com",
#             role=1,
#             reporting_manager=1,
#         ),
#         Employee(
#             staff_id=2,
#             staff_fname="Jane",
#             staff_lname="Smith",
#             dept="HR",
#             position="Manager",
#             country="SG",
#             email="jane.smith@example.com",
#             role=1,
#             reporting_manager=1,
#         ),
#         Employee(
#             staff_id=3,
#             staff_fname="Alice",
#             staff_lname="Brown",
#             dept="Finance",
#             position="Manager",
#             country="SG",
#             email="alice.brown@example.com",
#             role=1,
#             reporting_manager=1,
#         ),
#     ]


#     test_db.add(auth_record)
#     test_db.add_all(employees)
#     test_db.commit()
@pytest.fixture
def seed_data(test_db):
    # Create auth records
    auth_records = [
        Auth(email="manager.test@example.com", hashed_password="hashed_pwd"),
        Auth(email="delegate.test@example.com", hashed_password="hashed_pwd"),
    ]

    # Create employees
    employees = [
        Employee(
            staff_id=1,
            staff_fname="John",
            staff_lname="Doe",
            dept="IT",
            position="Manager",
            country="SG",
            email="john.doe@example.com",
            role=1,
            reporting_manager=1,
        ),
        Employee(
            staff_id=2,
            staff_fname="Jane",
            staff_lname="Smith",
            dept="HR",
            position="Manager",
            country="SG",
            email="jane.smith@example.com",
            role=1,
            reporting_manager=1,
        ),
        Employee(
            staff_id=3,
            staff_fname="Alice",
            staff_lname="Brown",
            dept="Finance",
            position="Manager",
            country="SG",
            email="alice.brown@example.com",
            role=1,
            reporting_manager=1,
        ),
    ]

    # Add records to database
    test_db.add_all(auth_records)
    test_db.add_all(employees)
    test_db.commit()

    # Return the test data for reference if needed
    return {"auth_records": auth_records, "employees": employees}


@pytest.fixture
def mock_employee():
    return MagicMock(
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


@pytest.fixture
def mock_manager():
    return MagicMock(
        staff_id=2, staff_fname="Jane", staff_lname="Smith", email="jane.smith@example.com"
    )


def test_get_manager_by_subordinate_id_auto_approve(test_db):
    assert get_manager_by_subordinate_id(test_db, 130002) is None


def test_get_manager_by_subordinate_id_non_existent_employee(test_db):
    with patch("src.employees.services.get_employee_by_id", return_value=None):
        with pytest.raises(EmployeeNotFoundException) as excinfo:
            get_manager_by_subordinate_id(test_db, 999)
        assert str(excinfo.value) == "Employee not found"


def test_get_employee_by_id_exists(test_db, seed_data):
    employee = get_employee_by_id(test_db, 1)
    assert employee.staff_id == 1


def test_get_employee_by_id_not_found(test_db):
    with pytest.raises(EmployeeNotFoundException):
        get_employee_by_id(test_db, 999)


def test_get_peers_by_staff_id_with_peers(test_db, seed_data):
    peers = get_peers_by_staff_id(test_db, 1)
    assert len(peers) > 0


def test_get_peers_by_staff_id_no_peers(test_db):
    # This will raise EmployeeNotFoundException because the employee doesn't exist
    with pytest.raises(EmployeeNotFoundException) as excinfo:
        get_peers_by_staff_id(test_db, 999)
    assert str(excinfo.value) == "Employee not found"


@pytest.mark.asyncio
async def test_delegate_manager_existing_delegation(test_db, seed_data):
    # First create a delegation
    delegate_log = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    test_db.add(delegate_log)
    test_db.commit()

    # Now try to create the same delegation again
    result = await delegate_manager(1, 2, test_db)
    assert result == "Delegation already exists for either the manager or delegatee."


def test_get_manager_with_valid_subordinate(test_db, seed_data):
    # Create manager
    manager = Employee(
        staff_id=10,
        staff_fname="Manager",
        staff_lname="Test",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager.test@example.com",
        role=1,
        reporting_manager=10,  # Self-reporting for manager
    )

    # Create subordinate reporting to manager
    subordinate = Employee(
        staff_id=11,
        staff_fname="Sub",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="sub.test@example.com",
        role=2,
        reporting_manager=10,  # Reports to manager
    )

    test_db.add_all([manager, subordinate])
    test_db.commit()

    result = get_manager_by_subordinate_id(test_db, 11)  # Use subordinate ID
    assert result is not None
    returned_manager, peers = result
    assert isinstance(returned_manager, Employee)
    assert isinstance(peers, list)


def test_get_manager_no_manager_available(test_db, seed_data):
    with pytest.raises(EmployeeNotFoundException):
        get_manager_by_subordinate_id(test_db, 999)


@pytest.mark.asyncio
async def test_delegate_manager_new_delegation(test_db, seed_data):
    # Ensure we have valid employees in the database
    employee1 = Employee(
        staff_id=4,  # Use a new ID not in seed data
        staff_fname="Test",
        staff_lname="Manager",
        email="test.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    employee2 = Employee(
        staff_id=5,  # Use a new ID not in seed data
        staff_fname="Test",
        staff_lname="Delegate",
        email="test.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    test_db.add_all([employee1, employee2])
    test_db.commit()

    with patch(
        "src.employees.services.craft_email_content_for_delegation"
    ) as mock_craft_email, patch("src.employees.services.send_email") as mock_send_email:
        mock_craft_email.return_value = ("Subject", "Content")

        # Use the new employee IDs
        result = await delegate_manager(4, 5, test_db)

        assert result is not None
        assert isinstance(result, DelegateLog)
        mock_send_email.assert_called()


@pytest.mark.asyncio
async def test_delegate_manager_existing_delegation(test_db, seed_data):
    # First create a delegation where manager_id=1 is already involved
    delegate_log = DelegateLog(
        manager_id=1,  # Manager is already delegating
        delegate_manager_id=3,
        status_of_delegation=DelegationStatus.pending,
    )
    test_db.add(delegate_log)
    test_db.commit()

    # Try to create another delegation with the same manager
    result = await delegate_manager(1, 2, test_db)
    assert result == "Delegation already exists for either the manager or delegatee."

    # Also try with the delegate manager being already involved
    another_delegate_log = DelegateLog(
        manager_id=4,
        delegate_manager_id=2,  # This person is already a delegate
        status_of_delegation=DelegationStatus.pending,
    )
    test_db.add(another_delegate_log)
    test_db.commit()

    # Try to create a delegation where delegate is already involved
    result = await delegate_manager(5, 2, test_db)
    assert result == "Delegation already exists for either the manager or delegatee."


@pytest.mark.asyncio
async def test_delegate_manager_exception_handling(test_db, seed_data):
    with patch("src.employees.crud.create_delegation") as mock_create_delegation:
        mock_create_delegation.side_effect = Exception("Database Error")
        with pytest.raises(Exception) as exc_info:
            await delegate_manager(1, 3, test_db)
        assert str(exc_info.value) == "Database Error"


@pytest.mark.asyncio
async def test_process_delegation_status_accept(test_db, seed_data):
    # Create a delegation log first
    delegate_log = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    test_db.add(delegate_log)
    test_db.commit()

    with patch(
        "src.employees.services.craft_email_content_for_delegation"
    ) as mock_craft_email, patch("src.employees.services.send_email") as mock_send_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await process_delegation_status(2, DelegationApprovalStatus.accept, test_db)

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.accepted
        mock_send_email.assert_called()


@pytest.mark.asyncio
async def test_process_delegation_status_reject(test_db, seed_data):
    # Create a pending delegation first
    delegate_log = DelegateLog(
        manager_id=1,  # This manager exists in seed_data
        delegate_manager_id=2,  # This is the delegate who will reject
        status_of_delegation=DelegationStatus.pending,
    )
    test_db.add(delegate_log)
    test_db.commit()

    with patch(
        "src.employees.services.craft_email_content_for_delegation"
    ) as mock_craft_email, patch("src.employees.services.send_email") as mock_send_email:
        mock_craft_email.return_value = ("Subject", "Content")

        # Process delegation status for staff_id 2 (the delegate)
        result = await process_delegation_status(2, DelegationApprovalStatus.reject, test_db)

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.rejected
        mock_send_email.assert_called()


@pytest.mark.asyncio
async def test_process_delegation_status_log_not_found(test_db):
    # Pass in a staff ID with no delegation log
    result = await process_delegation_status(999, DelegationApprovalStatus.reject, test_db)
    assert result == "Delegation log not found."


# Test case for when manager lookup returns None
def test_get_manager_by_subordinate_id_no_manager(test_db):
    # Create employee with no manager
    employee = Employee(
        staff_id=12,
        staff_fname="No",
        staff_lname="Manager",
        dept="IT",
        position="Staff",
        country="SG",
        email="no.manager@example.com",
        role=2,
        reporting_manager=None,
    )
    test_db.add(employee)
    test_db.commit()

    result = get_manager_by_subordinate_id(test_db, 12)
    assert result is None


# Test case for branch where manager exists but has no peers


# Test for employee locked in delegation
def test_get_manager_by_subordinate_id_locked_peers(test_db):
    # Create manager and peers
    manager = Employee(
        staff_id=15,
        staff_fname="Team",
        staff_lname="Manager",
        dept="IT",
        position="Manager",
        country="SG",
        email="team.manager@example.com",
        role=1,
    )

    peer1 = Employee(
        staff_id=16,
        staff_fname="Locked",
        staff_lname="Peer",
        dept="IT",
        position="Staff",
        country="SG",
        email="locked.peer@example.com",
        role=2,
        reporting_manager=15,
    )

    # Create delegation log to lock peer1
    delegation = DelegateLog(
        manager_id=16,
        delegate_manager_id=17,
        status_of_delegation=DelegationStatus.accepted,
    )

    test_db.add_all([manager, peer1, delegation])
    test_db.commit()

    manager_result, unlocked_peers = get_manager_by_subordinate_id(test_db, 16)
    assert manager_result is not None
    assert peer1 not in unlocked_peers


def test_view_delegations_empty(test_db):
    result = view_delegations(1, test_db)
    assert result["sent_delegations"] == []
    assert result["pending_approval_delegations"] == []


def test_view_delegations_with_data(test_db):
    # Create test employees
    manager = Employee(
        staff_id=20,
        staff_fname="View",
        staff_lname="Manager",
        email="view.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    delegate = Employee(
        staff_id=21,
        staff_fname="View",
        staff_lname="Delegate",
        email="view.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    # Create delegation log
    delegation = DelegateLog(
        manager_id=20,
        delegate_manager_id=21,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )

    test_db.add_all([manager, delegate, delegation])
    test_db.commit()

    result = view_delegations(20, test_db)
    assert len(result["sent_delegations"]) == 1
    assert len(result["pending_approval_delegations"]) == 0


def test_view_all_delegations(test_db):
    # Create test employees
    manager = Employee(
        staff_id=30,
        staff_fname="All",
        staff_lname="Manager",
        email="all.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    delegate = Employee(
        staff_id=31,
        staff_fname="All",
        staff_lname="Delegate",
        email="all.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    # Create both sent and received delegations
    sent_delegation = DelegateLog(
        manager_id=30,
        delegate_manager_id=31,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )

    received_delegation = DelegateLog(
        manager_id=31,
        delegate_manager_id=30,
        status_of_delegation=DelegationStatus.accepted,
        date_of_delegation=datetime.now(),
    )

    test_db.add_all([manager, delegate, sent_delegation, received_delegation])
    test_db.commit()

    result = view_all_delegations(30, test_db)
    assert len(result["sent_delegations"]) == 1
    assert len(result["received_delegations"]) == 1


@pytest.mark.asyncio
async def test_undelegate_manager_success(test_db):
    # Create test data
    manager = Employee(
        staff_id=40,
        staff_fname="Un",
        staff_lname="Manager",
        email="un.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    delegate = Employee(
        staff_id=41,
        staff_fname="Un",
        staff_lname="Delegate",
        email="un.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    delegation = DelegateLog(
        manager_id=40,
        delegate_manager_id=41,
        status_of_delegation=DelegationStatus.accepted,
        date_of_delegation=datetime.now(),
    )

    test_db.add_all([manager, delegate, delegation])
    test_db.commit()

    with patch("src.employees.services.send_email") as mock_send_email, patch(
        "src.employees.services.craft_email_content_for_delegation"
    ) as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await undelegate_manager(40, test_db)
        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.undelegated
        mock_send_email.assert_called()


@pytest.mark.asyncio
async def test_undelegate_manager_not_found(test_db):
    result = await undelegate_manager(999, test_db)
    assert result == "Delegation log not found."


@pytest.mark.asyncio
async def test_undelegate_manager_not_accepted(test_db):
    # Create delegation with pending status
    manager = Employee(
        staff_id=50,
        staff_fname="Pending",
        staff_lname="Manager",
        email="pending.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    delegation = DelegateLog(
        manager_id=50,
        delegate_manager_id=51,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )

    test_db.add_all([manager, delegation])
    test_db.commit()

    result = await undelegate_manager(50, test_db)
    assert result == "Delegation must be approved to undelegate."


def test_get_manager_by_subordinate_id_with_single_subordinate(test_db):
    """Test case for when a manager has exactly one subordinate.

    We expect to get the manager and all employees under that manager (including the manager
    themselves)
    """
    # Create a manager with only one subordinate
    manager = Employee(
        staff_id=13,
        staff_fname="Solo",
        staff_lname="Manager",
        dept="IT",
        position="Manager",
        country="SG",
        email="solo.manager@example.com",
        role=1,
        reporting_manager=13,  # Self-reporting
    )

    subordinate = Employee(
        staff_id=14,
        staff_fname="Sub",
        staff_lname="Employee",
        dept="IT",
        position="Staff",
        country="SG",
        email="sub.employee@example.com",
        role=2,
        reporting_manager=13,
    )

    test_db.add_all([manager, subordinate])
    test_db.commit()

    manager_result, peers = get_manager_by_subordinate_id(test_db, 14)
    assert manager_result is not None
    assert manager_result.staff_id == 13
    # We expect both the manager and subordinate in the peers list
    assert len(peers) == 2
    peer_ids = {peer.staff_id for peer in peers}
    assert peer_ids == {13, 14}


@pytest.mark.asyncio
async def test_process_delegation_status_invalid_input(test_db, seed_data):
    """Test case for when an invalid DelegationApprovalStatus is provided.

    Instead of raising an exception, we should test for the actual behavior.
    """
    # Create a pending delegation
    delegate_log = DelegateLog(
        manager_id=1,
        delegate_manager_id=2,
        status_of_delegation=DelegationStatus.pending,
    )
    test_db.add(delegate_log)
    test_db.commit()

    # Create a status that is not part of DelegationApprovalStatus enum
    result = await process_delegation_status(2, "invalid_status", test_db)
    # The function likely returns the delegation log without changing its status
    assert isinstance(result, DelegateLog)
    assert result.status_of_delegation == DelegationStatus.pending


@pytest.mark.asyncio
async def test_process_delegation_status_missing_description(test_db, seed_data):
    """Test rejection without providing a description."""
    # Create a pending delegation
    delegate_log = DelegateLog(
        manager_id=1,
        delegate_manager_id=2,
        status_of_delegation=DelegationStatus.pending,
    )
    test_db.add(delegate_log)
    test_db.commit()

    with patch(
        "src.employees.services.craft_email_content_for_delegation"
    ) as mock_craft_email, patch("src.employees.services.send_email") as mock_send_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await process_delegation_status(
            2, DelegationApprovalStatus.reject, test_db, description=None
        )

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.rejected
        mock_send_email.assert_called()


def test_view_delegations_with_no_employee_info(test_db):
    """Test viewing delegations when employee information is missing."""
    # Create a delegation log without corresponding employee records
    delegation = DelegateLog(
        manager_id=999,
        delegate_manager_id=998,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )

    test_db.add(delegation)
    test_db.commit()

    result = view_delegations(999, test_db)
    assert isinstance(result, dict)
    assert "sent_delegations" in result
    assert "pending_approval_delegations" in result
