import pytest
from src.arrangements.exceptions import ArrangementNotFoundError, ArrangementActionNotAllowedError


def test_arrangement_not_found_error():
    # Given
    arrangement_id = 42

    # When & Then
    with pytest.raises(ArrangementNotFoundError) as exc_info:
        raise ArrangementNotFoundError(arrangement_id)

    # Assert
    assert str(exc_info.value) == f"Arrangement with ID {arrangement_id} not found"


def test_arrangement_action_not_allowed_error_approve():
    # Given
    arrangement_id = 42
    action = "approve"

    # When & Then
    with pytest.raises(ArrangementActionNotAllowedError) as exc_info:
        raise ArrangementActionNotAllowedError(arrangement_id, action)

    # Assert
    assert str(exc_info.value) == f"Arrangement with ID {arrangement_id} is not in pending status"


def test_arrangement_action_not_allowed_error_reject():
    # Given
    arrangement_id = 42
    action = "reject"

    # When & Then
    with pytest.raises(ArrangementActionNotAllowedError) as exc_info:
        raise ArrangementActionNotAllowedError(arrangement_id, action)

    # Assert
    assert str(exc_info.value) == f"Arrangement with ID {arrangement_id} is not in pending status"


def test_arrangement_action_not_allowed_error_default():
    # Given
    arrangement_id = 42
    action = "other_action"

    # When & Then
    with pytest.raises(ArrangementActionNotAllowedError) as exc_info:
        raise ArrangementActionNotAllowedError(arrangement_id, action)

    # Assert
    assert str(exc_info.value) == "Default message"
