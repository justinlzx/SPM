import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, Query
from typing import List, Optional

from src.arrangements import crud
from src.arrangements.commons.models import LatestArrangement, ArrangementLog
from src.arrangements.commons.dataclasses import (
    ArrangementFilters,
    ArrangementResponse,
    CreateArrangementRequest,
    RecurringRequestDetails,
    CreatedRecurringRequest,
)
from src.arrangements.commons.enums import Action, ApprovalStatus, WfhType, RecurringFrequencyUnit
from src.employees.models import Employee
from src.auth.models import Auth
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, Query
from typing import List, Optional


@pytest.fixture
def mock_base():
    with patch("sqlalchemy.orm.declarative_base") as mock:
        yield mock


@pytest.fixture
def mock_auth():
    auth = MagicMock(spec=Auth)
    auth.email = "test@example.com"
    auth.hashed_password = "hashed_password"
    return auth


@pytest.fixture
def mock_employee():
    employee = MagicMock(spec=Employee)
    employee.staff_id = 100
    employee.staff_fname = "John"
    employee.staff_lname = "Doe"
    employee.dept = "IT"
    employee.email = "john.doe@example.com"
    employee.manager_staff_id = 200
    employee.reporting_manager = MagicMock()
    type(Employee).manager_staff_id = MagicMock()
    return employee


@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=Session)
    # Create a chain of mock returns
    query_mock = MagicMock(spec=Query)
    filter_mock = MagicMock(spec=Query)
    update_mock = MagicMock()
    order_by_mock = MagicMock()

    query_mock.filter = MagicMock(return_value=filter_mock)
    query_mock.order_by = MagicMock(return_value=order_by_mock)
    filter_mock.update = update_mock

    session.query = MagicMock(return_value=query_mock)
    session.add = MagicMock()
    session.commit = MagicMock()
    session.flush = MagicMock()
    session.rollback = MagicMock()

    return session


@pytest.fixture
def mock_latest_arrangement(mock_employee):
    arrangement = MagicMock(spec=LatestArrangement)
    # Set basic properties
    arrangement.arrangement_id = 1
    arrangement.update_datetime = datetime.now()
    arrangement.requester_staff_id = mock_employee.staff_id
    arrangement.wfh_date = date(2024, 1, 1)
    arrangement.wfh_type = WfhType.FULL
    arrangement.current_approval_status = ApprovalStatus.PENDING_APPROVAL
    arrangement.approving_officer = 200
    arrangement.reason_description = "Test reason"
    arrangement.latest_log_id = None
    arrangement.delegate_approving_officer = None
    arrangement.batch_id = None
    arrangement.supporting_doc_1 = None
    arrangement.supporting_doc_2 = None
    arrangement.supporting_doc_3 = None
    arrangement.status_reason = None

    # Set relationships
    arrangement.requester_info = mock_employee
    arrangement.approving_officer_info = mock_employee
    arrangement.delegate_approving_officer_info = None

    # Mock __dict__ to return all attributes
    arrangement.__dict__.update(arrangement.__dict__)
    return arrangement


@pytest.fixture
def mock_arrangement_log(mock_employee):
    log = MagicMock(spec=ArrangementLog)
    log.log_id = 1
    log.arrangement_id = 1
    log.update_datetime = datetime.now()
    log.approval_status = ApprovalStatus.PENDING_APPROVAL.value  # Use .value for enum
    log.reason_description = "Test reason"
    log.requester_staff_id = mock_employee.staff_id
    log.wfh_date = date(2024, 1, 1)
    log.wfh_type = WfhType.FULL
    log.action = Action.CREATE
    log.previous_approval_status = None
    log.updated_approval_status = ApprovalStatus.PENDING_APPROVAL
    log.approving_officer = 200
    log.supporting_doc_1 = None
    log.supporting_doc_2 = None
    log.supporting_doc_3 = None
    return log


# Test Classes
class TestGetArrangementById:
    def test_success(self, mock_db_session, mock_latest_arrangement):
        # Arrange
        mock_db_session.query.return_value.get.return_value = mock_latest_arrangement

        # Act
        result = crud.get_arrangement_by_id(mock_db_session, arrangement_id=1)

        # Assert
        assert result == mock_latest_arrangement.__dict__
        mock_db_session.query.assert_called_once_with(LatestArrangement)
        mock_db_session.query.return_value.get.assert_called_once_with(1)

    def test_not_found(self, mock_db_session):
        # Arrange
        mock_db_session.query.return_value.get.return_value = None

        # Act
        result = crud.get_arrangement_by_id(mock_db_session, arrangement_id=999)

        # Assert
        assert result is None


class TestGetArrangements:
    @pytest.fixture
    def mock_filters(self):
        return ArrangementFilters(
            current_approval_status=[ApprovalStatus.PENDING_APPROVAL],
            name=None,
            wfh_type=None,
            start_date=None,
            end_date=None,
            reason=None,
            department=None,
        )

    def test_get_arrangements_with_staff_id(
        self, mock_db_session, mock_latest_arrangement, mock_filters
    ):
        # Arrange
        mock_db_session.query.return_value.all.return_value = [mock_latest_arrangement]

        # Act
        result = crud.get_arrangements(mock_db_session, staff_ids=100, filters=mock_filters)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_latest_arrangement.__dict__
        mock_db_session.query.assert_called_once_with(LatestArrangement)

    def test_get_arrangements_with_filters(
        self, mock_db_session, mock_latest_arrangement, mock_filters
    ):
        # Arrange
        mock_filters.name = "John"
        mock_filters.wfh_type = [WfhType.FULL]
        mock_filters.start_date = date(2024, 1, 1)
        mock_filters.end_date = date(2024, 1, 31)
        mock_db_session.query.return_value.all.return_value = [mock_latest_arrangement]

        # Act
        result = crud.get_arrangements(mock_db_session, staff_ids=[100], filters=mock_filters)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_latest_arrangement.__dict__


class TestCreateArrangementLog:
    @patch("src.arrangements.crud.models.ArrangementLog")
    def test_success(
        self, mock_log_class, mock_db_session, mock_latest_arrangement, mock_arrangement_log
    ):
        # Arrange
        mock_log_class.return_value = mock_arrangement_log
        mock_db_session.add = MagicMock()
        mock_db_session.flush = MagicMock()

        # Act
        result = crud.create_arrangement_log(
            mock_db_session, mock_latest_arrangement, Action.CREATE, ApprovalStatus.PENDING_APPROVAL
        )

        # Assert
        assert result == mock_arrangement_log
        mock_db_session.add.assert_called_once_with(mock_arrangement_log)
        mock_db_session.flush.assert_called_once()

    @patch("src.arrangements.crud.models.ArrangementLog")
    def test_database_error(self, mock_log_class, mock_db_session, mock_latest_arrangement):
        # Arrange
        mock_db_session.add.side_effect = SQLAlchemyError("Database error")
        mock_db_session.rollback = MagicMock()

        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            crud.create_arrangement_log(
                mock_db_session,
                mock_latest_arrangement,
                Action.CREATE,
                ApprovalStatus.PENDING_APPROVAL,
            )

        mock_db_session.rollback.assert_called_once()

    @patch("src.arrangements.crud.models.ArrangementLog")
    def test_database_error_during_create(
        self, mock_log_class, mock_db_session, mock_latest_arrangement
    ):
        # Arrange
        error_to_raise = SQLAlchemyError("Database error")
        mock_log_class.side_effect = error_to_raise

        # Act & Assert
        with pytest.raises(SQLAlchemyError) as exc_info:
            crud.create_arrangement_log(
                mock_db_session,
                mock_latest_arrangement,
                Action.CREATE,
                ApprovalStatus.PENDING_APPROVAL,
            )

        # Assert that the error was the one we raised
        assert exc_info.value == error_to_raise
        mock_db_session.rollback.assert_called_once()


class TestGetArrangements:
    def test_get_arrangements_with_reason_filter(self, mock_db_session, mock_latest_arrangement):
        # Create chain of mocks
        mock_query = MagicMock()
        mock_joined = MagicMock()
        mock_filtered = MagicMock()

        # Set up the chain
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_joined
        mock_joined.filter.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered  # For additional filters
        mock_filtered.all.return_value = [mock_latest_arrangement]

        filters = ArrangementFilters(reason="Test reason")
        result = crud.get_arrangements(mock_db_session, staff_ids=[100], filters=filters)

        assert len(result) == 1
        assert result[0] == mock_latest_arrangement.__dict__
        mock_db_session.query.assert_called_once()

    def test_get_arrangements_with_department_filter(
        self, mock_db_session, mock_latest_arrangement
    ):
        # Create chain of mocks
        mock_query = MagicMock()
        mock_joined = MagicMock()
        mock_filtered = MagicMock()

        # Set up the chain
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_joined
        mock_joined.filter.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered  # For additional filters
        mock_filtered.all.return_value = [mock_latest_arrangement]

        filters = ArrangementFilters(department="IT")
        result = crud.get_arrangements(mock_db_session, staff_ids=[100], filters=filters)

        assert len(result) == 1
        assert result[0] == mock_latest_arrangement.__dict__
        mock_db_session.query.assert_called_once()

    def test_get_arrangements_without_staff_ids(self, mock_db_session, mock_latest_arrangement):
        # Test getting all arrangements without staff_ids filter
        result = crud.get_arrangements(mock_db_session)
        assert isinstance(result, list)

    def test_get_arrangements_without_filters(self, mock_db_session, mock_latest_arrangement):
        # Test getting arrangements without any filters
        result = crud.get_arrangements(mock_db_session, staff_ids=[100])
        assert isinstance(result, list)


class TestGetTeamArrangements:
    def test_get_team_arrangements(self, mock_db_session, mock_employee):
        # Mock team members query result
        mock_db_session.query().filter().all.return_value = [(1,), (2,)]

        filters = ArrangementFilters()
        result = crud.get_team_arrangements(
            mock_db_session, staff_id=mock_employee.staff_id, filters=filters
        )

        assert isinstance(result, list)
        mock_db_session.query.assert_called()


class TestGetArrangementLogs:
    def test_get_arrangement_logs(self, mock_db_session, mock_arrangement_log):
        # Set up the mock chain
        mock_query = mock_db_session.query.return_value
        mock_order = mock_query.order_by.return_value
        mock_order.all.return_value = [mock_arrangement_log]

        result = crud.get_arrangement_logs(mock_db_session)

        assert len(result) == 1
        assert result[0] == mock_arrangement_log.__dict__


class TestCreateRecurringRequest:
    @patch("src.arrangements.crud.models.RecurringRequest")
    def test_create_recurring_request_success(self, mock_request_class, mock_db_session):
        # Create the request
        request = RecurringRequestDetails(
            requester_staff_id=100,
            reason_description="Test recurring",
            start_date=date(2024, 1, 1),
            recurring_frequency_number=1,
            recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
            recurring_occurrences=4,
            request_datetime=datetime.now(),
        )

        # Create a mock recurring request instance with the right attributes
        mock_recurring_request = Mock()
        mock_recurring_request.__dict__ = {
            "batch_id": 1,
            "requester_staff_id": request.requester_staff_id,
            "start_date": request.start_date,
            "recurring_frequency_number": request.recurring_frequency_number,
            "recurring_frequency_unit": request.recurring_frequency_unit,
            "recurring_occurrences": request.recurring_occurrences,
            "request_datetime": request.request_datetime,
            "reason_description": request.reason_description,
        }

        # Instead of mocking class_mapper, let's mock the actual model class
        # and its instantiation
        def create_mock_request(**kwargs):
            mock_recurring_request.__dict__.update(kwargs)
            return mock_recurring_request

        mock_request_class.side_effect = create_mock_request

        # Mock the DB behavior
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.refresh = MagicMock()

        with patch("sqlalchemy.orm.class_mapper") as mock_mapper:
            # Create a mock mapper that looks like a SQLAlchemy mapper
            attrs_mock = MagicMock()
            attrs_mock.keys.return_value = mock_recurring_request.__dict__.keys()
            mock_mapper.return_value.attrs = attrs_mock

            # Execute test
            result = crud.create_recurring_request(mock_db_session, request)

            # Verify results
            assert isinstance(result, CreatedRecurringRequest)
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            assert mock_db_session.refresh.called

            # Verify the created recurring request has the expected values
            assert result.batch_id == 1
            assert result.requester_staff_id == request.requester_staff_id
            assert result.start_date == request.start_date
            assert result.recurring_frequency_number == request.recurring_frequency_number
            assert result.recurring_frequency_unit == request.recurring_frequency_unit
            assert result.recurring_occurrences == request.recurring_occurrences
            assert result.reason_description == request.reason_description

    def test_create_recurring_request_error(self, mock_db_session):
        mock_db_session.add.side_effect = SQLAlchemyError()

        with pytest.raises(SQLAlchemyError):
            crud.create_recurring_request(
                mock_db_session,
                RecurringRequestDetails(
                    requester_staff_id=100,
                    start_date=date(2024, 1, 1),
                    recurring_frequency_number=1,
                    recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
                    recurring_occurrences=4,
                    request_datetime=datetime.now(),
                    reason_description="Test",
                ),
            )

        mock_db_session.rollback.assert_called_once()


class TestUpdateArrangementApprovalStatus:
    def test_update_approval_status_success(self, mock_db_session, mock_latest_arrangement):
        # Set up mock chain
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.update.return_value = None
        mock_query.get.return_value = mock_latest_arrangement

        arrangement_response = ArrangementResponse(
            arrangement_id=1,
            update_datetime=datetime.now(),
            requester_staff_id=100,
            wfh_date=date(2024, 1, 1),
            wfh_type=WfhType.FULL,
            current_approval_status=ApprovalStatus.APPROVED,
            approving_officer=200,
        )

        result = crud.update_arrangement_approval_status(
            mock_db_session, arrangement_response, Action.APPROVE, ApprovalStatus.PENDING_APPROVAL
        )

        assert result == mock_latest_arrangement.__dict__
        mock_db_session.commit.assert_called_once()

    def test_update_approval_status_error(self, mock_db_session):
        mock_db_session.query().filter().update.side_effect = SQLAlchemyError()

        with pytest.raises(SQLAlchemyError):
            crud.update_arrangement_approval_status(
                mock_db_session,
                ArrangementResponse(
                    arrangement_id=1,
                    update_datetime=datetime.now(),
                    requester_staff_id=100,
                    wfh_date=date(2024, 1, 1),
                    wfh_type=WfhType.FULL,
                    current_approval_status=ApprovalStatus.APPROVED,
                    approving_officer=200,
                ),
                Action.APPROVE,
                ApprovalStatus.PENDING_APPROVAL,
            )

        mock_db_session.rollback.assert_called_once()

    def test_update_approval_status_not_found(self, mock_db_session):
        # Set up mock chain correctly
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.update.return_value = None
        mock_query.get.return_value = None  # Arrangement not found

        # Create the arrangement response
        arrangement_response = ArrangementResponse(
            arrangement_id=999,
            update_datetime=datetime.now(),
            requester_staff_id=100,
            wfh_date=date(2024, 1, 1),
            wfh_type=WfhType.FULL,
            current_approval_status=ApprovalStatus.APPROVED,
            approving_officer=200,
        )

        result = crud.update_arrangement_approval_status(
            mock_db_session, arrangement_response, Action.APPROVE, ApprovalStatus.PENDING_APPROVAL
        )

        assert result is None
        # The update should still be attempted
        mock_filter.update.assert_called_once()
        # But commit should not be called since no arrangement was found
        mock_db_session.commit.assert_not_called()
