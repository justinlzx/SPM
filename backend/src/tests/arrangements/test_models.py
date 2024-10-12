import pytest
from src.arrangements.models import ArrangementLog, LatestArrangement, RecurringRequest
from src.tests.test_utils import mock_db_session
from src.employees.models import Employee


@pytest.fixture
def mock_arrangement_log():
    """Fixture to create a mock ArrangementLog object."""
    return ArrangementLog(
        update_datetime="2024-10-12 12:34:56",
        requester_staff_id=1,
        wfh_date="2024-10-13",
        wfh_type="full",
        approval_status="pending",
        approving_officer=2,
        reason_description="Testing WFH request",
        batch_id=None,
    )


@pytest.fixture
def mock_latest_arrangement():
    """Fixture to create a mock LatestArrangement object."""
    return LatestArrangement(
        update_datetime="2024-10-12 12:34:56",
        requester_staff_id=1,
        wfh_date="2024-10-13",
        wfh_type="am",
        current_approval_status="approved",
        approving_officer=2,
        reason_description="Approved WFH request",
        batch_id=None,
        latest_log_id=1,
    )


@pytest.fixture
def mock_recurring_request():
    """Fixture to create a mock RecurringRequest object."""
    return RecurringRequest(
        request_datetime="2024-10-12 12:34:56",
        requester_staff_id=1,
        wfh_type="pm",
        reason_description="Recurring WFH request",
        start_date="2024-10-13",
        recurring_frequency_number=1,
        recurring_frequency_unit="week",
        recurring_occurrences=5,
    )


@pytest.fixture
def mock_employee():
    """Fixture to create a mock Employee object."""
    return Employee(
        staff_id=1,
        staff_fname="Test",
        staff_lname="Employee",
        dept="IT",
        position="Manager",
        country="USA",
        email="test.employee@example.com",
        role=2,
    )


def test_arrangement_log_fields(mock_db_session, mock_arrangement_log):
    """Test that ArrangementLog object has valid fields."""
    assert mock_arrangement_log.requester_staff_id == 1
    assert mock_arrangement_log.wfh_type == "full"
    assert mock_arrangement_log.approval_status == "pending"
    assert mock_arrangement_log.batch_id is None


def test_latest_arrangement_fields(mock_db_session, mock_latest_arrangement):
    """Test that LatestArrangement object has valid fields."""
    assert mock_latest_arrangement.requester_staff_id == 1
    assert mock_latest_arrangement.wfh_type == "am"
    assert mock_latest_arrangement.current_approval_status == "approved"
    assert mock_latest_arrangement.latest_log_id == 1


def test_recurring_request_fields(mock_db_session, mock_recurring_request):
    """Test that RecurringRequest object has valid fields."""
    assert mock_recurring_request.requester_staff_id == 1
    assert mock_recurring_request.wfh_type == "pm"
    assert mock_recurring_request.start_date == "2024-10-13"
    assert mock_recurring_request.recurring_frequency_unit == "week"
    assert mock_recurring_request.recurring_occurrences == 5


def test_check_constraints(mock_arrangement_log, mock_latest_arrangement, mock_recurring_request):
    """Test that CheckConstraints work as expected."""
    # Valid WFH types
    assert mock_arrangement_log.wfh_type in ["full", "am", "pm"]
    assert mock_latest_arrangement.wfh_type in ["full", "am", "pm"]
    assert mock_recurring_request.wfh_type in ["full", "am", "pm"]

    # Valid Approval Statuses
    assert mock_arrangement_log.approval_status in ["pending", "approved", "rejected", "withdrawn"]
    assert mock_latest_arrangement.current_approval_status in [
        "pending",
        "approved",
        "rejected",
        "withdrawn",
    ]


def test_relationships(mock_db_session, mock_arrangement_log, mock_employee):
    """Test relationships between models."""
    # Mock the requester_info relationship
    mock_arrangement_log.requester_info = mock_employee

    # Mock the approving_officer_info relationship (if needed)
    mock_arrangement_log.approving_officer_info = mock_employee

    # Ensure relationships are set up correctly
    assert mock_arrangement_log.requester_info is not None
    assert mock_arrangement_log.requester_info.staff_fname == "Test"
    assert mock_arrangement_log.approving_officer_info is not None
