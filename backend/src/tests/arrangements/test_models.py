# import pytest
# from src.employees.models import Employee

# from src.arrangements.commons.models import (
#     ArrangementLog,
#     LatestArrangement,
#     RecurringRequest,
# )


# @pytest.fixture
# def mock_arrangement_log():
#     """Fixture to create a mock ArrangementLog object."""
#     return ArrangementLog(
#         update_datetime="2024-10-12 12:34:56",
#         requester_staff_id=1,
#         wfh_date="2024-10-13",
#         wfh_type="full",
#         approval_status="pending",
#         approving_officer=2,
#         reason_description="Testing WFH request",
#         batch_id=None,
#     )


# @pytest.fixture
# def mock_latest_arrangement():
#     """Fixture to create a mock LatestArrangement object."""
#     return LatestArrangement(
#         update_datetime="2024-10-12 12:34:56",
#         requester_staff_id=1,
#         wfh_date="2024-10-13",
#         wfh_type="am",
#         current_approval_status="approved",
#         approving_officer=2,
#         delegate_approving_officer=3,  # Include delegate_approving_officer
#         reason_description="Approved WFH request",
#         batch_id=None,
#         latest_log_id=1,
#     )


# @pytest.fixture
# def mock_recurring_request():
#     """Fixture to create a mock RecurringRequest object."""
#     return RecurringRequest(
#         request_datetime="2024-10-12 12:34:56",
#         requester_staff_id=1,
#         wfh_type="pm",
#         reason_description="Recurring WFH request",
#         start_date="2024-10-13",
#         recurring_frequency_number=1,
#         recurring_frequency_unit="week",
#         recurring_occurrences=5,
#     )


# @pytest.fixture
# def mock_employee():
#     """Fixture to create a mock Employee object."""
#     return Employee(
#         staff_id=1,
#         staff_fname="Test",
#         staff_lname="Employee",
#         dept="IT",
#         position="Manager",
#         country="USA",
#         email="test.employee@example.com",
#         role=2,
#     )


# def test_arrangement_log_fields(mock_db_session, mock_arrangement_log):
#     """Test that ArrangementLog object has valid fields."""
#     assert mock_arrangement_log.requester_staff_id == 1
#     assert mock_arrangement_log.wfh_type == "full"
#     assert mock_arrangement_log.approval_status == "pending approval"
#     assert mock_arrangement_log.batch_id is None


# def test_latest_arrangement_fields(mock_db_session, mock_latest_arrangement):
#     """Test that LatestArrangement object has valid fields."""
#     assert mock_latest_arrangement.requester_staff_id == 1
#     assert mock_latest_arrangement.wfh_type == "am"
#     assert mock_latest_arrangement.current_approval_status == "approved"
#     assert mock_latest_arrangement.latest_log_id == 1
#     assert (
#         mock_latest_arrangement.delegate_approving_officer == 3
#     )  # Test for delegate_approving_officer


# def test_recurring_request_fields(mock_db_session, mock_recurring_request):
#     """Test that RecurringRequest object has valid fields."""
#     assert mock_recurring_request.requester_staff_id == 1
#     assert mock_recurring_request.wfh_type == "pm"
#     assert mock_recurring_request.start_date == "2024-10-13"
#     assert mock_recurring_request.recurring_frequency_unit == "week"
#     assert mock_recurring_request.recurring_occurrences == 5


# def test_check_constraints(mock_arrangement_log, mock_latest_arrangement, mock_recurring_request):
#     """Test that CheckConstraints work as expected."""
#     # Valid WFH types
#     assert mock_arrangement_log.wfh_type in ["full", "am", "pm"]
#     assert mock_latest_arrangement.wfh_type in ["full", "am", "pm"]
#     assert mock_recurring_request.wfh_type in ["full", "am", "pm"]

#     # Valid Approval Statuses
#     assert mock_arrangement_log.approval_status in [
#         "pending",
#         "approved",
#         "rejected",
#         "withdrawn",
#         "cancelled",
#     ]
#     assert mock_latest_arrangement.current_approval_status in [
#         "pending",
#         "approved",
#         "rejected",
#         "withdrawn",
#         "cancelled",
#     ]


# def test_relationships(mock_db_session, mock_arrangement_log, mock_employee):
#     """Test relationships between models."""
#     # Mock the requester_info relationship
#     mock_arrangement_log.requester_info = mock_employee

#     # Mock the approving_officer_info relationship (if needed)
#     mock_arrangement_log.approving_officer_info = mock_employee

#     # Ensure relationships are set up correctly
#     assert mock_arrangement_log.requester_info is not None
#     assert mock_arrangement_log.requester_info.staff_fname == "Test"
#     assert mock_arrangement_log.approving_officer_info is not None


# def test_delegate_relationship(mock_db_session, mock_latest_arrangement, mock_employee):
#     """Test relationship for delegate_approving_officer."""
#     # Mock the delegate_approving_officer_info relationship
#     mock_latest_arrangement.delegate_approving_officer_info = mock_employee

#     # Ensure the relationship is set up correctly
#     assert mock_latest_arrangement.delegate_approving_officer_info is not None
#     assert mock_latest_arrangement.delegate_approving_officer_info.staff_fname == "Test"

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.employees.models import Employee

from ...database import Base
from src.arrangements.commons.models import ArrangementLog, LatestArrangement, RecurringRequest
from src.arrangements.commons.enums import Action, ApprovalStatus, RecurringFrequencyUnit, WfhType
from src.auth.models import Auth


@pytest.fixture(scope="function")
def engine():
    """Create a new in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL query logging
    )
    # Create all tables
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Creates a new database session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_auth(db_session):
    """Create a test auth record."""
    auth = Auth(email="test@example.com", hashed_password="hashed_password_here")
    db_session.add(auth)
    db_session.commit()
    return auth


@pytest.fixture(scope="function")
def test_employee(db_session, test_auth):
    """Create a test employee for use in tests."""
    employee = Employee(
        staff_id=100,
        staff_fname="Test",
        staff_lname="Employee",
        dept="IT",
        position="Developer",
        country="Singapore",
        email=test_auth.email,  # Use the email from test_auth
        role=1,
    )
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture(scope="function")
def test_approver(db_session):
    """Create a test approver for use in tests."""
    auth = Auth(email="approver@example.com", hashed_password="hashed_password_here")
    db_session.add(auth)

    approver = Employee(
        staff_id=200,
        staff_fname="Test",
        staff_lname="Approver",
        dept="HR",
        position="Manager",
        country="Singapore",
        email=auth.email,
        role=2,
    )
    db_session.add(approver)
    db_session.commit()
    return approver


@pytest.fixture(scope="function")
def test_delegate_approver(db_session):
    """Create a test delegate approver for use in tests."""
    auth = Auth(email="delegate@example.com", hashed_password="hashed_password_here")
    db_session.add(auth)

    delegate = Employee(
        staff_id=300,
        staff_fname="Test",
        staff_lname="Delegate",
        dept="HR",
        position="Supervisor",
        country="Singapore",
        email=auth.email,
        role=2,
    )
    db_session.add(delegate)
    db_session.commit()
    return delegate


# Helper functions for creating test data
def create_test_arrangement(db_session, employee, approver=None, **kwargs):
    """Helper function to create a test arrangement with default values."""
    default_values = {
        "update_datetime": datetime.now(),
        "requester_staff_id": employee.staff_id,
        "wfh_date": "2024-11-05",
        "wfh_type": WfhType.FULL,
        "current_approval_status": ApprovalStatus.PENDING_APPROVAL,
        "approving_officer": approver.staff_id if approver else None,
    }
    default_values.update(kwargs)

    arrangement = LatestArrangement(**default_values)
    db_session.add(arrangement)
    db_session.commit()
    return arrangement


def create_test_log(db_session, arrangement, employee, **kwargs):
    """Helper function to create a test arrangement log with default values."""
    default_values = {
        "update_datetime": datetime.now(),
        "arrangement_id": arrangement.arrangement_id,
        "requester_staff_id": employee.staff_id,
        "wfh_date": arrangement.wfh_date,
        "wfh_type": arrangement.wfh_type,
        "action": Action.CREATE,
        "updated_approval_status": ApprovalStatus.PENDING_APPROVAL,
    }
    default_values.update(kwargs)

    log = ArrangementLog(**default_values)
    db_session.add(log)
    db_session.commit()
    return log


def create_test_recurring_request(db_session, employee, **kwargs):
    """Helper function to create a test recurring request with default values."""
    default_values = {
        "request_datetime": "2024-11-05 10:00:00",
        "requester_staff_id": employee.staff_id,
        "start_date": "2024-11-05",
        "recurring_frequency_number": 1,
        "recurring_frequency_unit": RecurringFrequencyUnit.WEEKLY,
        "recurring_occurrences": 4,
    }
    default_values.update(kwargs)

    request = RecurringRequest(**default_values)
    db_session.add(request)
    db_session.commit()
    return request


class TestArrangementLog:
    def test_create_arrangement_log(self, db_session):
        """Test creating a basic arrangement log"""
        log = ArrangementLog(
            update_datetime=datetime.now(),
            arrangement_id=1,
            requester_staff_id=100,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            action=Action.CREATE,
            updated_approval_status=ApprovalStatus.PENDING_APPROVAL,
        )
        db_session.add(log)
        db_session.commit()

        assert log.log_id is not None
        assert log.action == Action.CREATE
        assert log.wfh_type == WfhType.FULL

    def test_required_fields(self, db_session):
        """Test that required fields raise appropriate errors when missing"""
        log = ArrangementLog(
            # Missing required fields
            wfh_date="2024-11-05",
        )
        with pytest.raises(IntegrityError):
            db_session.add(log)
            db_session.commit()

    def test_relationships(self, db_session, test_auth):
        """Test relationships with Employee model"""
        # Create employee with correct field names
        employee = Employee(
            staff_id=100,
            staff_fname="Test",
            staff_lname="Employee",
            dept="IT",
            position="Developer",
            country="Singapore",
            email=test_auth.email,
            role=1,
        )
        db_session.add(employee)
        db_session.commit()

        # Create the arrangement log
        log = ArrangementLog(
            update_datetime=datetime.now(),
            arrangement_id=1,
            requester_staff_id=employee.staff_id,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            action=Action.CREATE,
            updated_approval_status=ApprovalStatus.PENDING_APPROVAL,
        )
        db_session.add(log)
        db_session.commit()

        assert log.requester_info.staff_id == employee.staff_id
        assert log.requester_info.staff_fname == "Test"


class TestLatestArrangement:
    def test_create_latest_arrangement(self, db_session):
        """Test creating a basic latest arrangement"""
        arrangement = LatestArrangement(
            update_datetime=datetime.now(),
            requester_staff_id=100,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        )
        db_session.add(arrangement)
        db_session.commit()

        assert arrangement.arrangement_id is not None
        assert arrangement.wfh_type == WfhType.FULL

    def test_delegate_approving_officer(
        self, db_session, test_employee, test_approver, test_delegate_approver
    ):
        """Test delegate approving officer functionality"""
        # Create arrangement using existing fixtures
        arrangement = LatestArrangement(
            update_datetime=datetime.now(),
            requester_staff_id=test_employee.staff_id,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            approving_officer=test_approver.staff_id,
            delegate_approving_officer=test_delegate_approver.staff_id,
        )
        db_session.add(arrangement)
        db_session.commit()

        # Verify relationships
        assert arrangement.delegate_approving_officer == test_delegate_approver.staff_id
        assert arrangement.delegate_approving_officer_info is not None
        assert (
            arrangement.delegate_approving_officer_info.staff_id == test_delegate_approver.staff_id
        )


class TestRecurringRequest:
    def test_create_recurring_request(self, db_session):
        """Test creating a basic recurring request"""
        request = RecurringRequest(
            request_datetime="2024-11-05 10:00:00",
            requester_staff_id=100,
            start_date="2024-11-05",
            recurring_frequency_number=1,
            recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
            recurring_occurrences=4,
        )
        db_session.add(request)
        db_session.commit()

        assert request.batch_id is not None
        assert request.recurring_frequency_unit == RecurringFrequencyUnit.WEEKLY
        assert request.recurring_occurrences == 4

    def test_valid_frequency(self, db_session, test_employee):
        """Test that valid frequency values are accepted"""
        request = RecurringRequest(
            request_datetime="2024-11-05 10:00:00",
            requester_staff_id=test_employee.staff_id,
            start_date="2024-11-05",
            recurring_frequency_number=1,  # Valid frequency
            recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
            recurring_occurrences=4,
        )
        db_session.add(request)
        db_session.commit()

        assert request.recurring_frequency_number == 1

    def test_valid_request(self, db_session, test_employee):
        """Test creating a valid recurring request"""
        request = RecurringRequest(
            request_datetime="2024-11-05 10:00:00",
            requester_staff_id=test_employee.staff_id,
            start_date="2024-11-05",
            recurring_frequency_number=1,
            recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
            recurring_occurrences=4,
        )
        db_session.add(request)
        db_session.commit()

        assert request.batch_id is not None
        assert request.recurring_frequency_number == 1
        assert request.recurring_occurrences == 4
        assert request.recurring_frequency_unit == RecurringFrequencyUnit.WEEKLY


class TestIntegration:
    def test_full_workflow(self, db_session):
        """Test the complete workflow of creating a recurring request and its arrangements"""
        # Create a recurring request
        recurring_request = RecurringRequest(
            request_datetime="2024-11-05 10:00:00",
            requester_staff_id=100,
            start_date="2024-11-05",
            recurring_frequency_number=1,
            recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
            recurring_occurrences=4,
        )
        db_session.add(recurring_request)
        db_session.commit()

        # Create a latest arrangement linked to the recurring request
        arrangement = LatestArrangement(
            update_datetime=datetime.now(),
            requester_staff_id=100,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            batch_id=recurring_request.batch_id,
        )
        db_session.add(arrangement)
        db_session.commit()

        # Create a log entry for the arrangement
        log = ArrangementLog(
            update_datetime=datetime.now(),
            arrangement_id=arrangement.arrangement_id,
            requester_staff_id=100,
            wfh_date="2024-11-05",
            wfh_type=WfhType.FULL,
            action=Action.CREATE,
            updated_approval_status=ApprovalStatus.PENDING_APPROVAL,
            batch_id=recurring_request.batch_id,
        )
        db_session.add(log)
        db_session.commit()

        # Verify the relationships
        assert arrangement.batch_id == recurring_request.batch_id
        assert log.arrangement_id == arrangement.arrangement_id
        assert log.batch_id == recurring_request.batch_id
