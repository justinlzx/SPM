import pytest
from src.arrangements.commons.enums import Action, ApprovalStatus
from src.arrangements.commons.exceptions import (
    ArrangementActionNotAllowedException,
    ArrangementNotFoundException,
    S3UploadFailedException,
)


class TestArrangementNotFoundException:
    def test_init_with_arrangement_id(self):
        # Arrange
        arrangement_id = 123

        # Act
        exception = ArrangementNotFoundException(arrangement_id)

        # Assert
        assert str(exception) == "Arrangement with ID 123 not found"
        assert exception.message == "Arrangement with ID 123 not found"

    def test_is_exception_instance(self):
        # Arrange & Act
        exception = ArrangementNotFoundException(456)

        # Assert
        assert isinstance(exception, Exception)

    @pytest.mark.parametrize(
        "arrangement_id", [0, 999999, -1, 2**31 - 1]  # Test negative ID  # Test max 32-bit integer
    )
    def test_various_arrangement_ids(self, arrangement_id):
        # Act
        exception = ArrangementNotFoundException(arrangement_id)

        # Assert
        assert str(exception) == f"Arrangement with ID {arrangement_id} not found"


class TestArrangementActionNotAllowedException:
    def test_init_with_status_and_action(self):
        # Arrange
        current_status = ApprovalStatus.PENDING_APPROVAL
        action = Action.APPROVE

        # Act
        exception = ArrangementActionNotAllowedException(current_status, action)

        # Assert
        expected_message = f"Action {action} not allowed for current status {current_status}"
        assert str(exception) == expected_message
        assert exception.message == expected_message

    @pytest.mark.parametrize(
        "status,action",
        [
            (ApprovalStatus.PENDING_APPROVAL, Action.APPROVE),
            (ApprovalStatus.PENDING_WITHDRAWAL, Action.WITHDRAW),
            (ApprovalStatus.APPROVED, Action.WITHDRAW),
            (ApprovalStatus.REJECTED, Action.CREATE),
            (ApprovalStatus.WITHDRAWN, Action.CANCEL),
            (ApprovalStatus.CANCELLED, Action.CREATE),
        ],
    )
    def test_init_with_various_status_and_actions(self, status, action):
        # Act
        exception = ArrangementActionNotAllowedException(status, action)

        # Assert
        expected_message = f"Action {action} not allowed for current status {status}"
        assert str(exception) == expected_message
        assert exception.message == expected_message

    def test_is_exception_instance(self):
        # Arrange & Act
        exception = ArrangementActionNotAllowedException(ApprovalStatus.REJECTED, Action.REJECT)

        # Assert
        assert isinstance(exception, Exception)

    def test_enum_values_in_message(self):
        # Arrange
        status = ApprovalStatus.PENDING_APPROVAL
        action = Action.CANCEL

        # Act
        exception = ArrangementActionNotAllowedException(status, action)

        # Assert
        assert str(status) in str(exception)
        assert str(action) in str(exception)


class TestS3UploadFailedException:
    @pytest.mark.parametrize(
        "error_message",
        [
            "Failed to upload file due to permissions",
            "Connection timeout",
            "Invalid credentials",
            "Bucket does not exist",
            "",  # Test empty message
            "Error: " * 100,  # Test long message
        ],
    )
    def test_init_with_various_messages(self, error_message):
        # Act
        exception = S3UploadFailedException(error_message)

        # Assert
        assert str(exception) == error_message
        assert exception.message == error_message

    def test_is_exception_instance(self):
        # Arrange & Act
        exception = S3UploadFailedException("Connection timeout")

        # Assert
        assert isinstance(exception, Exception)


def test_exceptions_can_be_caught():
    """Test that all custom exceptions can be caught as regular exceptions."""
    exceptions = [
        ArrangementNotFoundException(789),
        ArrangementActionNotAllowedException(ApprovalStatus.PENDING_APPROVAL, Action.REJECT),
        S3UploadFailedException("Test error"),
    ]

    for exc in exceptions:
        try:
            raise exc
        except Exception as e:
            assert str(e) == exc.message
