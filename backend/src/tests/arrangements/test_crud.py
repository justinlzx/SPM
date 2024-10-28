from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session
from src.arrangements import crud, models, schemas


@pytest.fixture
def mock_arrangement():
    return models.LatestArrangement(
        arrangement_id=1,
        requester_staff_id=140001,
        wfh_date=datetime(2024, 1, 15),
        wfh_type="full",
        approving_officer=151408,
        reason_description="Work from home request",
        update_datetime=datetime(2024, 1, 15),
        current_approval_status="pending",
        batch_id=1,
        supporting_doc_1=None,
        supporting_doc_2=None,
        supporting_doc_3=None,
        latest_log_id=789,
        requester_info=None,
    )


@pytest.fixture
def mock_arrangements():
    return [
        {
            "arrangement_id": 1,
            "requester_staff_id": 140001,
            "wfh_date": datetime(2024, 1, 15),
            "wfh_type": "full",
            "approving_officer": 151408,
            "reason_description": "Work from home request",
            "update_datetime": datetime(2024, 1, 15),
            "current_approval_status": "pending approval",
            "batch_id": 1,
            "supporting_doc_1": None,
            "supporting_doc_2": None,
            "supporting_doc_3": None,
            "latest_log_id": 789,
            "requester_info": {
                "staff_id": 140001,
                "staff_fname": "Derek",
                "staff_lname": "Tan",
                "email": "Derek.Tan@allinone.com.sg",
            },
        },
        {
            "arrangement_id": 2,
            "requester_staff_id": 151408,
            "wfh_date": datetime(2024, 1, 15),
            "wfh_type": "pm",
            "approving_officer": 130002,
            "reason_description": "Work from home request",
            "update_datetime": datetime(2024, 1, 16),
            "current_approval_status": "pending",
            "batch_id": 1,
            "supporting_doc_1": None,
            "supporting_doc_2": None,
            "supporting_doc_3": None,
            "latest_log_id": 123,
            "requester_info": {
                "staff_id": 151408,
                "staff_fname": "Philip",
                "staff_lname": "Lee",
                "email": "Philip.Lee@allinone.com.sg",
            },
        },
        {
            "arrangement_id": 3,
            "requester_staff_id": 151408,
            "wfh_date": datetime(2024, 1, 15),
            "wfh_type": "am",
            "approving_officer": 130002,
            "reason_description": "OOO",
            "update_datetime": datetime(2024, 1, 17),
            "current_approval_status": "rejected",
            "batch_id": 1,
            "supporting_doc_1": None,
            "supporting_doc_2": None,
            "supporting_doc_3": None,
            "latest_log_id": 123,
            "requester_info": {
                "staff_id": 151408,
                "staff_fname": "Philip",
                "staff_lname": "Lee",
                "email": "Philip.Lee@allinone.com.sg",
            },
        },
    ]


@pytest.fixture
def mock_create_arrangements_payload():
    """Create a sample arrangement payload."""
    return [
        {
            "requester_staff_id": 151408,  # Using Jack Sim's ID to test auto-approval
            "wfh_date": datetime(2024, 1, 15).date(),
            "wfh_type": "full",
            "approving_officer": 130002,
            "delegate_approving_officer": None,
            "reason_description": "Work from home request",
            "supporting_doc_1": "testfile1.pdf",
            "supporting_doc_2": "testfile2.pdf",
            "supporting_doc_3": None,
            "current_approval_status": "pending approval",
            "latest_log_id": 789,
        },
        {
            "requester_staff_id": 130002,  # Using Jack Sim's ID to test auto-approval
            "wfh_date": datetime(2024, 1, 15).date(),
            "wfh_type": "full",
            "approving_officer": 130002,
            "delegate_approving_officer": None,
            "reason_description": "Work from home request",
            "supporting_doc_1": "testfile1.pdf",
            "supporting_doc_2": "testfile2.pdf",
            "supporting_doc_3": None,
            "current_approval_status": "pending approval",
            "latest_log_id": 789,
        },
    ]


@pytest.fixture
def mock_db(mock_arrangements):
    """Create a mock database session with chainable query methods."""
    db = Mock(spec=Session)
    query = Mock(spec=Query)

    # Make all query methods chainable
    query.join.return_value = query
    query.filter.return_value = query
    query.all.return_value = mock_arrangements

    # Store the original filter method for verification
    query._filter = query.filter

    # Create a more sophisticated filter that can handle our actual filters
    def filtered_results(*args, **kwargs):
        # You could implement actual filtering logic here if needed
        query.filter_args = getattr(query, "filter_args", []) + [args]
        return query

    query.filter.side_effect = filtered_results
    db.query.return_value = query

    return db, query


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


@pytest.mark.parametrize(
    "staff_ids, filters, expected_arrangement_ids",
    [
        # Test vase 0: No filters
        ([], {}, [1, 2]),  # One filter call for staff_ids
        # Test case: Basic staff_ids only
        ([140001], {}, [1]),  # One filter call for staff_ids
        ([140001, 151408], {}, [1, 2]),  # One filter call for staff_ids
        # Test case: Name filter
        ([], {"name": "Philip"}, [2]),
        ([], {"name": "Sim"}, [1]),
        # Test case: Current_approval_status filter
        ([], {"current_approval_status": ["rejected"]}, [3]),
        ([], {"current_approval_status": ["pending", "rejected"]}, [1, 3]),
        # Test case: wfh_type filter
        ([], {"wfh_type": "full"}, [1]),
        ([], {"wfh_type": "am"}, [2]),
        ([], {"wfh_type": "pm"}, [3]),
        # Test case: start_date filter
        ([], {"start_date": datetime(2024, 1, 16)}, [2, 3]),
        # Test case: end_date filter
        ([], {"end_date": datetime(2024, 1, 15)}, [1, 2]),
        ([], {"end_date": datetime(2024, 1, 17)}, [1, 2, 3]),
        # Test case: start_date and end_date filter
        ([], {"start_date": datetime(2024, 1, 15), "end_date": datetime(2024, 1, 16)}, [1, 2]),
        # Test case 7:reason == OOO filter
        ([], {"reason": "OOO"}, [3]),
    ],
)
def test_get_arrangements(mock_db, staff_ids, filters, mock_arrangements, expected_arrangement_ids):

    # Unpack mock_db_session fixture
    db, query = mock_db

    filtered_query = query

    if staff_ids:
        filtered_query = filtered_query.filter.return_value

    filtered_query.all.return_value = [
        arrangement
        for arrangement in mock_arrangements
        if arrangement["arrangement_id"] in expected_arrangement_ids
    ]

    # Call the function with test parameters
    results = crud.get_arrangements(db, staff_ids, **filters)

    result_ids = [result["arrangement_id"] for result in results]
    # Verify final result
    assert result_ids == expected_arrangement_ids


def test_create_arrangement_log(mock_db_session, mock_arrangement, mock_arrangement_log):
    mock_db_session.add = MagicMock()
    mock_db_session.flush = MagicMock()
    mock_db_session.refresh = MagicMock()

    crud.fit_model_to_model = MagicMock(return_value=mock_arrangement_log)

    result = crud.create_arrangement_log(mock_db_session, mock_arrangement, "create")

    assert result == mock_arrangement_log
    mock_db_session.add.assert_called_once_with(mock_arrangement_log)
    mock_db_session.flush.assert_called_once()


@patch("src.arrangements.crud.create_arrangement_log")
@pytest.mark.parametrize(
    "index, num_results, approval_status",
    [
        # test case non jack sim
        (0, 1, "pending approval"),
        # test case not jack sim multiple
        (None, 2, "pending approval"),
        # test case jack sim
        (1, 1, "approved"),
    ],
)
def test_create_arrangements_success(
    mock_create_log,
    mock_db_session,
    index,
    mock_create_arrangements_payload,
    approval_status,
    num_results,
):
    """Test successful creation of arrangements."""
    # Arrange
    mock_log = Mock()
    mock_log.log_id = 123
    mock_create_log.return_value = mock_log

    mock_create_arrangements_payload_schema = [
        models.LatestArrangement(**arrangement) for arrangement in mock_create_arrangements_payload
    ]

    if index is not None:
        mock_create_arrangements_payload_schema = [mock_create_arrangements_payload_schema[index]]

    # Act
    result = crud.create_arrangements(mock_db_session, mock_create_arrangements_payload_schema)

    # Assert
    assert len(result) == num_results
    assert result == mock_create_arrangements_payload_schema
    assert mock_create_arrangements_payload_schema[0].current_approval_status == approval_status
    assert mock_create_arrangements_payload_schema[0].latest_log_id == 123


@patch("src.arrangements.crud.create_arrangement_log")
def test_create_arrangements_sqlalchemy_error(mock_db_session, mock_create_arrangements_payload):
    """Test handling of database errors."""
    mock_create_arrangements_payload_schema = [
        models.LatestArrangement(**arrangement) for arrangement in mock_create_arrangements_payload
    ]
    # Arrange
    mock_db_session.flush.side_effect = SQLAlchemyError("Database error")

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        crud.create_arrangements(mock_db_session, mock_create_arrangements_payload_schema)

    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()


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


def test_get_arrangements_multiple_status(mock_db_session, mock_arrangements):
    # Mock the query object behavior
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.join.return_value = mock_query  # Mock join
    mock_query.filter.return_value = mock_query  # Mock filter
    mock_query.all.return_value = mock_arrangements  # Return mocked arrangements

    # Call the function with multiple approval statuses
    result = crud.get_arrangements(
        mock_db_session, staff_ids=[12345, 130002], current_approval_status=["pending", "approved"]
    )

    # Assertions on the final result
    mock_db_session.query.assert_called_once_with(models.LatestArrangement)
    mock_query.join.assert_called_once()

    assert len(mock_query.filter.call_args_list) == 2  # Ensure filter was used twice
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


def test_get_arrangements_no_approval_status(mock_db_session, mock_arrangements):
    # Mock the query object behavior
    mock_query = MagicMock()
    mock_db_session.query.return_value = mock_query
    mock_query.join.return_value = mock_query  # Mock join
    mock_query.filter.return_value = mock_query  # Mock filter
    mock_query.all.return_value = mock_arrangements  # Return mocked arrangements

    # Call the function without current_approval_status
    result = crud.get_arrangements(
        mock_db_session, staff_ids=[12345, 130002], current_approval_status=None
    )

    # Assertions on the final result
    mock_db_session.query.assert_called_once_with(models.LatestArrangement)
    mock_query.join.assert_called_once()
    mock_query.filter.assert_called_once()  # No filter call expected
    assert result == mock_arrangements  # Ensure the result matches
