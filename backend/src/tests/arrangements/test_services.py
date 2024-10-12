import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from src.arrangements.services import (
    get_arrangement_by_id,
    get_personal_arrangements_by_filter,
    get_subordinates_arrangements,
    get_team_arrangements,
    create_arrangements_from_request,
    expand_recurring_arrangement,
    update_arrangement_approval_status,
)
from src.arrangements import exceptions as arrangement_exceptions
from src.employees import exceptions as employee_exceptions
from src.arrangements.models import LatestArrangement
from src.arrangements.schemas import ArrangementCreateWithFile, ArrangementUpdate


@pytest.fixture
def mock_db_session():
    # Mock the session for testing purposes
    return MagicMock()


# 1. get_arrangement_by_id
@patch("src.arrangements.crud.get_arrangement_by_id")
def test_get_arrangement_by_id_success(mock_get_arrangement_by_id, mock_db_session):
    mock_arrangement = MagicMock(spec=LatestArrangement)
    mock_get_arrangement_by_id.return_value = mock_arrangement

    result = get_arrangement_by_id(mock_db_session, arrangement_id=1)

    assert result == mock_arrangement
    mock_get_arrangement_by_id.assert_called_once_with(mock_db_session, 1)


@patch("src.arrangements.crud.get_arrangement_by_id", return_value=None)
def test_get_arrangement_by_id_not_found(mock_get_arrangement_by_id, mock_db_session):
    with pytest.raises(arrangement_exceptions.ArrangementNotFoundError):
        get_arrangement_by_id(mock_db_session, arrangement_id=999)


# 2. get_personal_arrangements_by_filter
@patch("src.arrangements.crud.get_arrangements_by_filter")
@patch("src.utils.convert_model_to_pydantic_schema")
def test_get_personal_arrangements_by_filter_success(
    mock_convert_model, mock_get_arrangements_by_filter, mock_db_session
):
    mock_arrangements = [MagicMock(spec=LatestArrangement)]
    mock_get_arrangements_by_filter.return_value = mock_arrangements
    mock_convert_model.return_value = ["arrangement_schema"]

    result = get_personal_arrangements_by_filter(mock_db_session, 1, ["approved"])

    assert result == ["arrangement_schema"]
    mock_get_arrangements_by_filter.assert_called_once_with(mock_db_session, 1, ["approved"])


# 3. get_subordinates_arrangements
@patch("src.employees.services.get_subordinates_by_manager_id")
@patch("src.arrangements.crud.get_arrangements_by_staff_ids")
@patch("src.utils.convert_model_to_pydantic_schema")
def test_get_subordinates_arrangements_success(
    mock_convert_model, mock_get_arrangements_by_staff_ids, mock_get_subordinates, mock_db_session
):
    mock_subordinates = [MagicMock(staff_id=1)]
    mock_get_subordinates.return_value = mock_subordinates
    mock_get_arrangements_by_staff_ids.return_value = [MagicMock(spec=LatestArrangement)]
    mock_convert_model.return_value = ["arrangement_schema"]

    result = get_subordinates_arrangements(
        mock_db_session, manager_id=1, current_approval_status=["approved"]
    )

    assert result == ["arrangement_schema"]
    mock_get_subordinates.assert_called_once_with(mock_db_session, 1)
    mock_get_arrangements_by_staff_ids.assert_called_once()


@patch("src.employees.services.get_subordinates_by_manager_id", return_value=[])
def test_get_subordinates_arrangements_manager_not_found(mock_get_subordinates, mock_db_session):
    with pytest.raises(employee_exceptions.ManagerNotFoundException):
        get_subordinates_arrangements(
            mock_db_session, manager_id=999, current_approval_status=["pending"]
        )
