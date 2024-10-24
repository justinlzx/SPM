from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from src.arrangements import crud, models, schemas


@pytest.fixture
def mock_arrangement():
    return models.LatestArrangement(
        arrangement_id=1, requester_staff_id=12345, current_approval_status="pending"
    )


@pytest.fixture
def mock_arrangements():
    return [
        models.LatestArrangement(
            arrangement_id=1, requester_staff_id=12345, current_approval_status="pending"
        ),
        models.LatestArrangement(
            arrangement_id=2, requester_staff_id=130002, current_approval_status="pending"
        ),
    ]


@pytest.fixture
def mock_arrangement_log():
    return models.ArrangementLog(
        log_id=1, approval_status="pending", update_datetime=datetime.utcnow()
    )


def test_create_arrangement_log_sqlalchemy_error(mock_db_session, mock_arrangement):
    # Simulate SQLAlchemyError being raised on db.add()
    mock_db_session.add.side_effect = SQLAlchemyError("Database Error")
    mock_db_session.commit.side_effect = SQLAlchemyError("Database Error")

    # Assert that the SQLAlchemyError is raised
    with pytest.raises(SQLAlchemyError):
        crud.create_arrangement_log(mock_db_session, mock_arrangement, "create")

    # Ensure rollback was called after the exception
    mock_db_session.rollback.assert_called_once()


def test_get_arrangement_by_id(mock_db_session, mock_arrangement):
    mock_db_session.query().get.return_value = mock_arrangement

    result = crud.get_arrangement_by_id(mock_db_session, arrangement_id=1)

    mock_db_session.query().get.assert_called_once_with(1)
    assert result == mock_arrangement


def test_get_arrangements_by_filter(mock_db_session, mock_arrangements):
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_arrangements

    result = crud.get_arrangements_by_filter(
        mock_db_session, requester_staff_id=12345, current_approval_status=["pending"]
    )

    mock_db_session.query.assert_called_once()
    mock_query.filter.assert_called()
    assert len(result) == 2


def test_get_arrangements_by_staff_ids(mock_db_session, mock_arrangements):
    # Mock the query object behavior
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.join.return_value = mock_query  # Mock join
    mock_query.where.return_value = mock_query  # Mock where
    mock_query.filter.return_value = mock_query  # Mock filter
    mock_query.all.return_value = mock_arrangements  # Return mocked arrangements

    # Call the function
    result = crud.get_arrangements_by_staff_ids(
        mock_db_session, staff_ids=[12345, 130002], current_approval_status=["pending"]
    )

    # Assertions on the final result
    mock_db_session.query.assert_called_once_with(models.LatestArrangement)
    mock_query.join.assert_called_once()
    mock_query.where.assert_called_once()  # Ensure where was used
    mock_query.filter.assert_called_once()  # Ensure filter was used
    assert result == mock_arrangements  # Ensure the result matches


def test_create_arrangement_log(mock_db_session, mock_arrangement, mock_arrangement_log):
    mock_db_session.add = MagicMock()
    mock_db_session.flush = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.fit_model_to_model = MagicMock(return_value=mock_arrangement_log)

    result = crud.create_arrangement_log(mock_db_session, mock_arrangement, "create")

    assert result == mock_arrangement_log
    mock_db_session.add.assert_called_once_with(mock_arrangement_log)
    mock_db_session.flush.assert_called_once()


def test_create_arrangements(mock_db_session, mock_arrangements, mock_arrangement_log):
    mock_db_session.add = MagicMock()
    mock_db_session.flush = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.fit_model_to_model = MagicMock(return_value=mock_arrangement_log)

    result = crud.create_arrangements(mock_db_session, mock_arrangements)

    assert len(result) == 2
    mock_db_session.add.assert_called()
    mock_db_session.flush.assert_called()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called()


def test_create_arrangements_sqlalchemy_error(mock_db_session, mock_arrangements):
    mock_db_session.add.side_effect = SQLAlchemyError("Database Error")

    with pytest.raises(SQLAlchemyError):
        crud.create_arrangements(mock_db_session, mock_arrangements)

    mock_db_session.rollback.assert_called_once()


def test_update_arrangement_approval_status(
    mock_db_session, mock_arrangement, mock_arrangement_log
):
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.create_arrangement_log = MagicMock(return_value=mock_arrangement_log)

    result = crud.update_arrangement_approval_status(mock_db_session, mock_arrangement, "approve")

    assert result == mock_arrangement
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_arrangement)


def test_update_arrangement_approval_status_sqlalchemy_error(mock_db_session, mock_arrangement):
    mock_db_session.commit.side_effect = SQLAlchemyError("Database Error")

    with pytest.raises(SQLAlchemyError):
        crud.update_arrangement_approval_status(mock_db_session, mock_arrangement, "approve")

    mock_db_session.rollback.assert_called_once()


def test_create_recurring_request_sqlalchemy_error(mock_db_session):
    # Simulate a SQLAlchemy error
    mock_db_session.add.side_effect = SQLAlchemyError("Database Error")

    # Arrange with required fields populated correctly
    request = schemas.ArrangementCreate(
        requester_staff_id=12345,
        wfh_date="2024-10-11",  # Should be a string, which is correct
        start_date="2024-10-11",  # Should be a string, which is correct
        wfh_type="full",  # Valid value: 'full', 'am', or 'pm'
        approving_officer=123,  # Should be an integer (staff ID), not a string
        reason_description="Working from home due to personal reasons.",  # Valid string
    )

    # Act and Assert
    with pytest.raises(SQLAlchemyError):
        crud.create_recurring_request(mock_db_session, request)

    mock_db_session.rollback.assert_called_once()


def test_create_recurring_request(mock_db_session):
    # Arrange
    mock_batch = models.RecurringRequest(
        requester_staff_id=12345,
        start_date="2024-10-11",  # Use a valid field like 'start_date'
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    # Arrange with correct values
    request = schemas.ArrangementCreate(
        requester_staff_id=12345,
        wfh_date="2024-10-11",
        start_date="2024-10-11",
        wfh_type="full",  # Valid value
        approving_officer=123,  # Valid value (integer)
        reason_description="Working from home due to personal reasons.",
    )

    # Mock fit_schema_to_model
    crud.fit_schema_to_model = MagicMock(return_value=mock_batch)

    # Act
    result = crud.create_recurring_request(mock_db_session, request)

    # Assert
    assert result == mock_batch
    mock_db_session.add.assert_called_once_with(mock_batch)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_batch)


def test_get_arrangements_by_filter_multiple_status(mock_db_session, mock_arrangements):
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_arrangements

    result = crud.get_arrangements_by_filter(
        mock_db_session, current_approval_status=["pending", "approved"]
    )

    mock_db_session.query.assert_called_once()
    mock_query.filter.assert_called()
    assert len(result) == 2


def test_create_arrangements_auto_approve_jack_sim(mock_db_session, mock_arrangement_log):
    jack_sim_arrangement = models.LatestArrangement(
        arrangement_id=3, requester_staff_id=130002, current_approval_status="pending"
    )
    mock_db_session.add = MagicMock()
    mock_db_session.flush = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.create_arrangement_log = MagicMock(return_value=mock_arrangement_log)

    result = crud.create_arrangements(mock_db_session, [jack_sim_arrangement])

    assert len(result) == 1
    assert result[0].current_approval_status == "approved"
    mock_db_session.add.assert_called()
    mock_db_session.flush.assert_called()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called()


def test_get_arrangements_by_staff_ids_multiple_status(mock_db_session, mock_arrangements):
    # Mock the query object behavior
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.join.return_value = mock_query  # Mock join
    mock_query.where.return_value = mock_query  # Mock where
    mock_query.filter.return_value = mock_query  # Mock filter
    mock_query.all.return_value = mock_arrangements  # Return mocked arrangements

    # Call the function with multiple approval statuses
    result = crud.get_arrangements_by_staff_ids(
        mock_db_session, staff_ids=[12345, 130002], current_approval_status=["pending", "approved"]
    )

    # Assertions on the final result
    mock_db_session.query.assert_called_once_with(models.LatestArrangement)
    mock_query.join.assert_called_once()
    mock_query.where.assert_called_once()  # Ensure where was used
    mock_query.filter.assert_called_once()  # Ensure filter was used
    assert result == mock_arrangements  # Ensure the result matches


def test_create_recurring_request_with_recurring(mock_db_session):
    mock_batch = models.RecurringRequest(
        requester_staff_id=12345,
        start_date="2024-10-11",
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    request = schemas.ArrangementCreate(
        requester_staff_id=12345,
        wfh_date="2024-10-11",
        start_date="2024-10-11",
        wfh_type="full",
        approving_officer=123,
        reason_description="Recurring WFH request",
        is_recurring=True,
        recurring_frequency_number=1,
        recurring_occurrences=5,
    )

    crud.fit_schema_to_model = MagicMock(return_value=mock_batch)

    result = crud.create_recurring_request(mock_db_session, request)

    assert result == mock_batch
    mock_db_session.add.assert_called_once_with(mock_batch)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_batch)


def test_get_arrangements_by_filter_no_requester(mock_db_session, mock_arrangements):
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_arrangements

    result = crud.get_arrangements_by_filter(
        mock_db_session, requester_staff_id=None, current_approval_status=["pending"]
    )

    mock_db_session.query.assert_called_once()
    mock_query.filter.assert_called()
    assert len(result) == 2


def test_create_arrangements_non_jack_sim(mock_db_session, mock_arrangements, mock_arrangement_log):
    mock_arrangement = models.LatestArrangement(
        arrangement_id=4, requester_staff_id=12345, current_approval_status="pending"
    )
    mock_db_session.add = MagicMock()
    mock_db_session.flush = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.create_arrangement_log = MagicMock(return_value=mock_arrangement_log)

    result = crud.create_arrangements(mock_db_session, [mock_arrangement])

    assert len(result) == 1
    assert result[0].current_approval_status == "pending"  # Not auto-approved for non-Jack Sim
    mock_db_session.add.assert_called()
    mock_db_session.flush.assert_called()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called()


def test_get_arrangements_by_filter_no_approval_status(mock_db_session, mock_arrangements):
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_arrangements

    # Call the function without current_approval_status
    result = crud.get_arrangements_by_filter(
        mock_db_session, requester_staff_id=12345, current_approval_status=None
    )

    mock_db_session.query.assert_called_once()
    mock_query.filter.assert_called_once_with(mock.ANY)  # Skip exact comparison
    assert len(result) == 2


def test_get_arrangements_by_staff_ids_no_approval_status(mock_db_session, mock_arrangements):
    # Mock the query object behavior
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.join.return_value = mock_query  # Mock join
    mock_query.where.return_value = mock_query  # Mock where
    mock_query.filter.return_value = mock_query  # Mock filter
    mock_query.all.return_value = mock_arrangements  # Return mocked arrangements

    # Call the function without current_approval_status
    result = crud.get_arrangements_by_staff_ids(
        mock_db_session, staff_ids=[12345, 130002], current_approval_status=None
    )

    # Assertions on the final result
    mock_db_session.query.assert_called_once_with(models.LatestArrangement)
    mock_query.join.assert_called_once()
    mock_query.where.assert_called_once()  # Ensure where was used
    mock_query.filter.assert_not_called()  # No filter call expected
    assert result == mock_arrangements  # Ensure the result matches
