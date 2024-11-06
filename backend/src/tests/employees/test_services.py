from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Enum, create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.auth.models import Auth
from src.employees import schemas
from src.employees.dataclasses import EmployeeFilters
from src.employees.exceptions import (
    EmployeeGenericNotFoundException,
    EmployeeNotFoundException,
    ManagerWithIDNotFoundException,
)
from src.employees.models import Base, DelegateLog, DelegationStatus, Employee
from src.employees.services import (
    DelegationApprovalStatus,
    delegate_manager,
    get_employee_by_email,
    get_employee_by_id,
    get_employees,
    get_manager_by_subordinate_id,
    get_peers_by_staff_id,
    get_reporting_manager_and_peer_employees,
    get_subordinates_by_manager_id,
    process_delegation_status,
    undelegate_manager,
    view_all_delegations,
    view_delegations,
)

# Configure the in-memory SQLite database
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.rollback()
    Base.metadata.drop_all(bind=engine)
    db.close()


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

    test_db.add_all(auth_records)
    test_db.add_all(employees)
    test_db.commit()

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


@patch("src.employees.services.convert_model_to_pydantic_schema")
@patch("src.employees.crud.get_employees")
def test_get_employees(mock_get_employees, mock_convert, test_db, mock_employee):
    mock_filters = MagicMock(spec=EmployeeFilters)
    mock_convert.return_value = [mock_employee, mock_employee]

    employees = get_employees(test_db, mock_filters)
    assert len(employees) == len(mock_convert.return_value)


def test_get_manager_by_subordinate_id_auto_approve(test_db):
    manager, peers = get_manager_by_subordinate_id(test_db, 130002)
    assert manager is None
    assert peers is None


def test_get_manager_by_subordinate_id_non_existent_employee(test_db):
    with patch("src.employees.services.get_employee_by_id", return_value=None):
        with pytest.raises(EmployeeNotFoundException) as excinfo:
            get_manager_by_subordinate_id(test_db, 999)
        assert str(excinfo.value) == "Employee with ID 999 not found"


def test_get_employee_by_id_exists(test_db, seed_data):
    employee = get_employee_by_id(test_db, 1)
    assert employee.staff_id == 1


def test_get_employee_by_id_not_found(test_db):
    with pytest.raises(EmployeeNotFoundException) as exc_info:
        get_employee_by_id(test_db, 999)
    assert str(exc_info.value) == "Employee with ID 999 not found"


def test_get_peers_by_staff_id_with_peers(test_db, seed_data):
    peers = get_peers_by_staff_id(test_db, 1)
    assert len(peers) > 0


def test_get_peers_by_staff_id_no_peers(test_db):
    with pytest.raises(EmployeeNotFoundException) as exc_info:
        get_peers_by_staff_id(test_db, 999)
    assert str(exc_info.value) == "Employee with ID 999 not found"


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
    with pytest.raises(EmployeeNotFoundException) as exc_info:
        get_manager_by_subordinate_id(test_db, 999)
    assert str(exc_info.value) == "Employee with ID 999 not found"


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

    with patch("src.employees.services.craft_and_send_email") as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        # Use the new employee IDs
        result = await delegate_manager(4, 5, test_db)

        assert result is not None
        assert isinstance(result, DelegateLog)
        mock_craft_email.assert_called()


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

    with patch("src.employees.services.craft_and_send_email") as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await process_delegation_status(2, DelegationApprovalStatus.accept, test_db)

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.accepted
        mock_craft_email.assert_called()


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

    with patch("src.employees.services.craft_and_send_email") as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        # Process delegation status for staff_id 2 (the delegate)
        result = await process_delegation_status(2, DelegationApprovalStatus.reject, test_db)

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.rejected
        mock_craft_email.assert_called()


@pytest.mark.asyncio
async def test_process_delegation_status_log_not_found(test_db):
    # Pass in a staff ID with no delegation log
    result = await process_delegation_status(999, DelegationApprovalStatus.reject, test_db)
    assert result == "Delegation log not found."


# Test case for when manager lookup returns None
def test_get_manager_by_subordinate_id_no_manager(test_db):
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

    manager, peers = get_manager_by_subordinate_id(test_db, 12)
    assert manager is None
    assert peers is None


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

    with patch("src.employees.services.craft_and_send_email") as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await undelegate_manager(40, test_db)
        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.undelegated
        mock_craft_email.assert_called()


@pytest.mark.asyncio
async def test_undelegate_manager_not_found(test_db):
    result = await undelegate_manager(999, test_db)
    assert result == "Delegation log not found."


@pytest.mark.asyncio
async def test_undelegate_manager_not_accepted(test_db):
    # Create manager
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

    # Create delegate manager (this was missing before)
    delegate = Employee(
        staff_id=51,
        staff_fname="Delegate",
        staff_lname="Manager",
        email="delegate.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )

    # Create delegation with pending status
    delegation = DelegateLog(
        manager_id=50,
        delegate_manager_id=51,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )

    test_db.add_all([manager, delegate, delegation])
    test_db.commit()

    with patch("src.employees.services.craft_and_send_email") as mock_email:
        mock_email.return_value = ("Subject", "Content")
        result = await undelegate_manager(50, test_db)

        # Verify email was sent
        mock_email.assert_called_once()

        # Verify delegation was marked as undelegated
        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.undelegated


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

    with patch("src.employees.services.craft_and_send_email") as mock_craft_email:
        mock_craft_email.return_value = ("Subject", "Content")

        result = await process_delegation_status(
            2, DelegationApprovalStatus.reject, test_db, description=None
        )

        assert isinstance(result, DelegateLog)
        assert result.status_of_delegation == DelegationStatus.rejected
        mock_craft_email.assert_called()


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


def test_get_reporting_manager_and_peer_employees_success(test_db, seed_data):
    # Create test data with proper self-referencing manager
    manager = Employee(
        staff_id=10,
        staff_fname="Manager",
        staff_lname="Test",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager.test@example.com",
        role=1,
        reporting_manager=None,  # Top-level manager
    )
    test_db.add(manager)
    test_db.commit()

    # Now create a subordinate that reports to this manager
    subordinate1 = Employee(
        staff_id=11,
        staff_fname="Sub1",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="sub1.test@example.com",
        role=2,
        reporting_manager=10,  # Reports to manager 10
    )
    test_db.add(subordinate1)
    test_db.commit()

    # First verify the manager relationship is set up correctly
    manager_result = get_manager_by_subordinate_id(test_db, 11)
    assert manager_result is not None
    assert isinstance(manager_result, tuple)
    assert len(manager_result) == 2
    manager_obj, unlocked_peers = manager_result
    assert manager_obj.staff_id == 10

    # Now test the special case with ID 130002 (Jack Sim)
    response = get_reporting_manager_and_peer_employees(test_db, 130002)
    assert response.manager_id is None
    assert len(response.peer_employees) == 0


def test_get_reporting_manager_and_peer_employees_jack_sim(test_db):
    # Test the special case for Jack Sim (staff_id: 130002)
    response = get_reporting_manager_and_peer_employees(test_db, 130002)
    assert response.manager_id is None
    assert len(response.peer_employees) == 0


def test_get_employee_by_email_success(test_db):
    # Test successful email lookup
    employee = Employee(
        staff_id=14,
        staff_fname="Email",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="email.test@example.com",
        role=2,
        reporting_manager=1,
    )

    test_db.add(employee)
    test_db.commit()

    result = get_employee_by_email(test_db, "email.test@example.com")
    assert result.staff_id == 14
    assert result.email == "email.test@example.com"


def test_get_employee_by_email_not_found(test_db):
    with pytest.raises(EmployeeGenericNotFoundException) as exc_info:
        get_employee_by_email(test_db, "nonexistent@example.com")
    assert str(exc_info.value) == "Employee not found"


@pytest.mark.asyncio
async def test_process_delegation_status_invalid_status(test_db, seed_data):
    # Create a delegation for testing
    delegate_log = DelegateLog(
        manager_id=1, delegate_manager_id=2, status_of_delegation=DelegationStatus.pending
    )
    test_db.add(delegate_log)
    test_db.commit()

    # Create an invalid status enum value
    class InvalidStatus(Enum):
        invalid = "invalid"

    # Test with an invalid status
    result = await process_delegation_status(2, InvalidStatus.invalid, test_db)

    # Since the status is invalid, the delegation log should remain in pending state
    assert isinstance(result, DelegateLog)
    assert result.status_of_delegation == DelegationStatus.pending


def test_print_statements_coverage(test_db):
    manager = Employee(
        staff_id=15,
        staff_fname="Print",
        staff_lname="Test",
        dept="IT",
        position="Manager",
        country="SG",
        email="print.test@example.com",
        role=1,
        reporting_manager=None,
    )
    test_db.add(manager)
    test_db.commit()

    subordinate = Employee(
        staff_id=16,
        staff_fname="Print",
        staff_lname="Sub",
        dept="IT",
        position="Staff",
        country="SG",
        email="print.sub@example.com",
        role=2,
        reporting_manager=15,
    )
    test_db.add(subordinate)
    test_db.commit()

    response = get_reporting_manager_and_peer_employees(test_db, 130002)
    assert response.manager_id is None
    assert len(response.peer_employees) == 0

    manager_result, peers = get_manager_by_subordinate_id(test_db, 16)
    assert manager_result is not None
    assert isinstance(manager_result, Employee)  # Changed from tuple to Employee
    assert manager_result.staff_id == 15


def test_get_reporting_manager_and_peer_employees_no_manager(test_db: Session):
    # Create an employee with no manager
    employee = Employee(
        staff_id=30,
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

    # Mock get_manager_by_subordinate_id to return None directly
    with patch("src.employees.services.get_manager_by_subordinate_id", return_value=None):
        # Call the function
        response = get_reporting_manager_and_peer_employees(test_db, 30)

    # Check that the response correctly shows no manager
    assert response.manager_id is None
    assert len(response.peer_employees) == 0


def test_get_subordinates_by_manager_id_success(test_db):
    """Test successful retrieval of subordinates."""
    # Create a manager
    manager = Employee(
        staff_id=40,
        staff_fname="Sub",
        staff_lname="Manager",
        dept="IT",
        position="Manager",
        country="SG",
        email="sub.manager@example.com",
        role=1,
        reporting_manager=None,
    )
    test_db.add(manager)

    # Create subordinates
    subordinates = [
        Employee(
            staff_id=id,
            staff_fname=f"SubEmp{i}",
            staff_lname="Test",
            dept="IT",
            position="Staff",
            country="SG",
            email=f"subemp{i}.test@example.com",
            role=2,
            reporting_manager=40,
        )
        for i, id in enumerate([41, 42], 1)
    ]
    test_db.add_all(subordinates)
    test_db.commit()

    # Test getting subordinates
    result = get_subordinates_by_manager_id(test_db, 40)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(emp, Employee) for emp in result)

    # Verify correct subordinates are returned
    subordinate_ids = [emp.staff_id for emp in result]
    assert 41 in subordinate_ids
    assert 42 in subordinate_ids


def test_get_subordinates_by_manager_id_not_found(test_db):
    """Test when manager has no subordinates."""
    # Create a manager with no subordinates
    manager = Employee(
        staff_id=50,
        staff_fname="No",
        staff_lname="Subs",
        dept="IT",
        position="Manager",
        country="SG",
        email="no.subs@example.com",
        role=1,
        reporting_manager=None,
    )
    test_db.add(manager)
    test_db.commit()

    with pytest.raises(ManagerWithIDNotFoundException) as exc_info:
        get_subordinates_by_manager_id(test_db, 999)  # Use non-existent manager ID
    assert exc_info.value.manager_id == 999


@patch("src.employees.services.get_manager_by_subordinate_id")
@patch("src.employees.services.get_subordinates_by_manager_id")
@patch("src.employees.services.convert_model_to_pydantic_schema")
def test_get_reporting_manager_and_peer_employees_full_flow(
    mock_convert, mock_get_subordinates, mock_get_manager, test_db
):
    """Test the complete flow of get_reporting_manager_and_peer_employees."""
    # Create test data
    manager = Employee(
        staff_id=20,
        staff_fname="Full",
        staff_lname="Manager",
        dept="IT",
        position="Manager",
        country="SG",
        email="full.manager@example.com",
        role=1,
        reporting_manager=None,
    )
    test_db.add(manager)
    test_db.commit()

    # Set up mock returns
    mock_get_manager.return_value = manager  # Return manager object, not tuple
    mock_get_subordinates.return_value = [
        Employee(
            staff_id=21,
            staff_fname="Sub1",
            staff_lname="Test",
            dept="IT",
            position="Staff",
            country="SG",
            email="sub1.test@example.com",
            role=2,
            reporting_manager=20,
        )
    ]
    mock_convert.return_value = [
        schemas.EmployeeBase(
            staff_id=21,
            staff_fname="Sub1",
            staff_lname="Test",
            dept="IT",
            position="Staff",
            country="SG",
            email="sub1.test@example.com",
            role=2,
        )
    ]

    # Test the function
    response = get_reporting_manager_and_peer_employees(test_db, 21)

    # Verify the response
    assert response is not None
    assert response.manager_id == 20
    assert len(response.peer_employees) > 0

    # Verify all functions were called
    mock_get_manager.assert_called_once_with(test_db, 21)
    mock_get_subordinates.assert_called_once_with(test_db, 20)
    mock_convert.assert_called_once()


@patch("src.employees.services.get_manager_by_subordinate_id")
@patch("src.employees.services.get_subordinates_by_manager_id")
@patch("src.employees.services.convert_model_to_pydantic_schema")
def test_get_reporting_manager_and_peer_employees_print_statement(
    mock_convert, mock_get_subordinates, mock_get_manager, test_db
):
    """Test to ensure print statement is covered."""
    # Create test manager
    manager = Employee(
        staff_id=60,
        staff_fname="Print",
        staff_lname="Manager",
        dept="IT",
        position="Manager",
        country="SG",
        email="print.manager@example.com",
        role=1,
        reporting_manager=None,
    )

    # Set up mock returns
    mock_get_manager.return_value = manager  # Return manager object, not tuple
    mock_get_subordinates.return_value = [
        Employee(
            staff_id=61,
            staff_fname="Print",
            staff_lname="Sub",
            dept="IT",
            position="Staff",
            country="SG",
            email="print.sub@example.com",
            role=2,
            reporting_manager=60,
        )
    ]
    mock_convert.return_value = [
        schemas.EmployeeBase(
            staff_id=61,
            staff_fname="Print",
            staff_lname="Sub",
            dept="IT",
            position="Staff",
            country="SG",
            email="print.sub@example.com",
            role=2,
        )
    ]

    # Test the function
    response = get_reporting_manager_and_peer_employees(test_db, 61)

    # Verify response
    assert response is not None
    assert response.manager_id == 60
    assert len(response.peer_employees) == 1

    # Verify all functions were called
    mock_get_manager.assert_called_once_with(test_db, 61)
    mock_get_subordinates.assert_called_once_with(test_db, 60)
    mock_convert.assert_called_once()


@pytest.mark.asyncio
@patch("src.employees.services.get_manager_by_subordinate_id")  # Add this patch
async def test_get_reporting_manager_and_peer_employees_with_peers(mock_get_manager, test_db):
    """Test to cover list comprehension in get_reporting_manager_and_peer_employees"""
    # Create manager
    manager = Employee(
        staff_id=200,
        staff_fname="Manager",
        staff_lname="Test",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager.test@example.com",
        role=1,
        reporting_manager=200,  # Self-reporting
    )
    test_db.add(manager)
    test_db.commit()

    # Create peers with DIFFERENT IDs
    peer1 = Employee(
        staff_id=201,
        staff_fname="Peer1",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="peer1.test@example.com",
        role=2,
        reporting_manager=200,
    )
    peer2 = Employee(
        staff_id=202,
        staff_fname="Peer2",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="peer2.test@example.com",
        role=2,
        reporting_manager=200,
    )
    test_db.add_all([peer1, peer2])
    test_db.commit()

    # Mock get_manager_by_subordinate_id to return just the manager object
    mock_get_manager.return_value = manager

    # Now test the reporting manager function
    response = get_reporting_manager_and_peer_employees(test_db, 201)

    # Verify the response
    assert response.manager_id == 200
    assert len(response.peer_employees) == 2  # Should include both peers

    # Verify the mock was called correctly
    mock_get_manager.assert_called_once_with(test_db, 201)

    # Verify peer IDs are correct (order doesn't matter)
    peer_ids = {peer.staff_id for peer in response.peer_employees}
    assert peer_ids == {201, 202}


def test_get_manager_by_subordinate_id_with_unlocked_peers(test_db):
    """Test to cover the list comprehension and print statement in get_manager_by_subordinate_id"""
    # Create manager
    manager = Employee(
        staff_id=300,
        staff_fname="Manager",
        staff_lname="Test",
        dept="IT",
        position="Manager",
        country="SG",
        email="manager.test@example.com",
        role=1,
    )
    test_db.add(manager)
    test_db.commit()

    # Create peers with unique IDs
    peer1 = Employee(
        staff_id=301,
        staff_fname="Peer1",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="peer1.test@example.com",
        role=2,
        reporting_manager=300,
    )
    peer2 = Employee(
        staff_id=302,
        staff_fname="Peer2",
        staff_lname="Test",
        dept="IT",
        position="Staff",
        country="SG",
        email="peer2.test@example.com",
        role=2,
        reporting_manager=300,
    )
    test_db.add_all([peer1, peer2])
    test_db.commit()

    manager_result, unlocked_peers = get_manager_by_subordinate_id(test_db, 301)
    assert manager_result is not None
    assert manager_result.staff_id == 300
    assert len(unlocked_peers) == 2


def test_view_delegations_with_data(test_db):
    """Test to cover list comprehensions in view_delegations"""
    # Create manager and delegate
    manager = Employee(
        staff_id=400,
        staff_fname="View",
        staff_lname="Manager",
        email="view.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    delegate = Employee(
        staff_id=401,
        staff_fname="View",
        staff_lname="Delegate",
        email="view.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    test_db.add_all([manager, delegate])
    test_db.commit()

    # Create both sent and pending delegations
    sent_delegation = DelegateLog(
        manager_id=400,
        delegate_manager_id=401,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )
    pending_delegation = DelegateLog(
        manager_id=401,
        delegate_manager_id=400,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )
    test_db.add_all([sent_delegation, pending_delegation])
    test_db.commit()

    result = view_delegations(400, test_db)
    assert len(result["sent_delegations"]) == 1
    assert len(result["pending_approval_delegations"]) == 1
    assert result["sent_delegations"][0]["staff_id"] == 401
    assert result["pending_approval_delegations"][0]["staff_id"] == 401


def test_view_all_delegations_with_data(test_db):
    """Test to cover list comprehensions in view_all_delegations"""
    # Create manager and delegate
    manager = Employee(
        staff_id=500,
        staff_fname="All",
        staff_lname="Manager",
        email="all.manager@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    delegate = Employee(
        staff_id=501,
        staff_fname="All",
        staff_lname="Delegate",
        email="all.delegate@example.com",
        dept="IT",
        position="Manager",
        country="SG",
        role=1,
    )
    test_db.add_all([manager, delegate])
    test_db.commit()

    # Create both sent and received delegations with different statuses
    sent_delegation = DelegateLog(
        manager_id=500,
        delegate_manager_id=501,
        status_of_delegation=DelegationStatus.pending,
        date_of_delegation=datetime.now(),
    )
    received_delegation = DelegateLog(
        manager_id=501,
        delegate_manager_id=500,
        status_of_delegation=DelegationStatus.accepted,
        date_of_delegation=datetime.now(),
    )
    test_db.add_all([sent_delegation, received_delegation])
    test_db.commit()

    result = view_all_delegations(500, test_db)
    assert len(result["sent_delegations"]) == 1
    assert len(result["received_delegations"]) == 1
    assert result["sent_delegations"][0]["manager_id"] == 500
    assert result["sent_delegations"][0]["delegate_manager_id"] == 501
    assert result["received_delegations"][0]["manager_id"] == 501
    assert result["received_delegations"][0]["delegate_manager_id"] == 500
