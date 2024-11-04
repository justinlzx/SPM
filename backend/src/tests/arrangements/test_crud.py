import pytest
from datetime import date, datetime
from unittest.mock import Mock, create_autospec, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query

from src.arrangements import crud
from src.arrangements.commons.models import LatestArrangement, ArrangementLog
from src.arrangements.commons.dataclasses import (
    ArrangementFilters,
    ArrangementResponse,
    CreateArrangementRequest,
)
from src.arrangements.commons.enums import Action, ApprovalStatus, WfhType
from src.employees.models import Employee
from src.auth.models import Auth


@pytest.fixture
def arrangement_dict():
    return {
        "arrangement_id": 1,
        "update_datetime": datetime.now(),
        "requester_staff_id": 100,
        "wfh_date": date(2024, 1, 1),
        "wfh_type": WfhType.FULL,
        "current_approval_status": ApprovalStatus.PENDING_APPROVAL,
        "approving_officer": 200,
        "latest_log_id": None,
        "delegate_approving_officer": None,
        "reason_description": "Test reason",
        "batch_id": None,
        "supporting_doc_1": None,
        "supporting_doc_2": None,
        "supporting_doc_3": None,
        "status_reason": None,
    }


@pytest.fixture
def mock_db_session(mock_query):
    session = MagicMock()
    session.query = MagicMock(return_value=mock_query)
    return session


@pytest.fixture
def mock_arrangement():
    arrangement = MagicMock()
    arrangement.__dict__ = {
        "arrangement_id": 1,
        "update_datetime": datetime.now(),
        "requester_staff_id": 100,
        "wfh_date": date(2024, 1, 1),
        "wfh_type": WfhType.FULL,
        "current_approval_status": ApprovalStatus.PENDING_APPROVAL,
    }
    return arrangement


@pytest.fixture
def mock_auth():
    mock = MagicMock(spec=Auth)
    mock.email = "test@example.com"
    return mock


@pytest.fixture
def mock_query():
    return MagicMock(spec=Query)


@pytest.fixture
def mock_latest_arrangement():
    arrangement_dict = {
        "arrangement_id": 1,
        "update_datetime": datetime.now(),
        "requester_staff_id": 100,
        "wfh_date": date(2024, 1, 1),
        "wfh_type": WfhType.FULL,
        "current_approval_status": ApprovalStatus.PENDING_APPROVAL,
        "approving_officer": 200,
        "latest_log_id": None,
        "delegate_approving_officer": None,
        "reason_description": "Test reason",
        "batch_id": None,
        "supporting_doc_1": None,
        "supporting_doc_2": None,
        "supporting_doc_3": None,
        "status_reason": None,
    }
    mock = MagicMock()
    mock.configure_mock(**arrangement_dict)
    mock.__dict__ = arrangement_dict
    return mock


@patch("src.arrangements.crud.models.LatestArrangement")
def test_get_arrangement_by_id(mock_latest, mock_db_session, mock_arrangement, mock_query):
    mock_query.get.return_value = mock_arrangement

    result = crud.get_arrangement_by_id(mock_db_session, 1)
    assert result == mock_arrangement.__dict__


class MockLatestArrangement:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@patch("src.arrangements.crud.models.LatestArrangement")
def test_get_arrangements_by_staff_ids_single_id(
    mock_latest, mock_db_session, mock_arrangement, mock_query
):
    mock_query.all.return_value = [mock_arrangement]
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query

    filters = ArrangementFilters(
        current_approval_status=[ApprovalStatus.PENDING_APPROVAL],
        name=None,
        wfh_type=None,
        start_date=None,
        end_date=None,
        reason=None,
    )

    result = crud.get_arrangements_by_staff_ids(mock_db_session, 100, filters)
    assert result == [mock_arrangement.__dict__]


def test_get_arrangements_by_staff_ids_with_filters(mock_db_session, mock_latest_arrangement):
    mock_db_session.query.return_value.all.return_value = [mock_latest_arrangement]

    filters = ArrangementFilters(
        current_approval_status=[ApprovalStatus.PENDING_APPROVAL],
        name="Test",
        wfh_type=["FULL"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        reason="Test",
    )

    result = crud.get_arrangements_by_staff_ids(mock_db_session, [100, 101], filters)
    assert result == [mock_latest_arrangement.__dict__]


@patch("src.arrangements.crud.Employee")
@patch("src.arrangements.commons.models.LatestArrangement")
def test_create_arrangement_log(
    mock_arrangement_cls, mock_employee, mock_db_session, mock_latest_arrangement
):
    with patch("src.arrangements.commons.models.ArrangementLog") as mock_log_cls:
        mock_log = MagicMock()
        mock_log_cls.return_value = mock_log

        log = crud.create_arrangement_log(
            mock_db_session, mock_latest_arrangement, Action.CREATE, ApprovalStatus.PENDING_APPROVAL
        )

        assert log == mock_log
        mock_db_session.add.assert_called_once()


@patch("src.arrangements.crud.class_mapper")
@patch("src.arrangements.crud.models.LatestArrangement")
def test_create_arrangements_success(mock_latest, mock_mapper, mock_db_session):
    # Mock the class_mapper to avoid UnmappedClassError
    mock_latest.return_value = MagicMock()
    mock_latest.return_value.__dict__ = {}

    arrangement_request = CreateArrangementRequest(
        requester_staff_id=100,
        wfh_date=date(2024, 1, 1),
        wfh_type=WfhType.FULL,
        reason_description="Test",
        update_datetime=datetime.now(),
        is_recurring=False,
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        approving_officer=200,
        recurring_frequency_number=None,
        recurring_frequency_unit=None,
        recurring_occurrences=None,
    )

    with patch("src.arrangements.crud.create_arrangement_log") as mock_log:
        mock_log.return_value = MagicMock(log_id=1)
        result = crud.create_arrangements(mock_db_session, [arrangement_request])

    assert len(result) == 1
    mock_db_session.commit.assert_called_once()


@patch("src.arrangements.crud.models.LatestArrangement")
def test_update_arrangement_approval_status(
    mock_latest, mock_db_session, mock_arrangement, mock_query
):
    mock_query.get.return_value = mock_arrangement
    mock_query.filter.return_value = mock_query
    mock_query.update.return_value = None

    arrangement_response = ArrangementResponse(
        arrangement_id=1,
        current_approval_status=ApprovalStatus.APPROVED,
        update_datetime=datetime.now(),
        requester_staff_id=100,
        wfh_date=date(2024, 1, 1),
        wfh_type=WfhType.FULL,
        approving_officer=200,
    )

    with patch("src.arrangements.crud.create_arrangement_log") as mock_log:
        mock_log.return_value = MagicMock(log_id=1)
        result = crud.update_arrangement_approval_status(
            mock_db_session, arrangement_response, Action.APPROVE, ApprovalStatus.PENDING_APPROVAL
        )

    assert isinstance(result, dict)
    mock_db_session.commit.assert_called_once()
