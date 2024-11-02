import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.arrangements.scheduler import app, auto_reject_old_requests, process_single_request
from src.arrangements.commons.enums import Action, ApprovalStatus
from src.arrangements.commons.dataclasses import UpdateArrangementRequest
from src.database import get_db


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock_session = Mock()
    # Mock the return of query and filter methods
    mock_query = Mock()
    mock_filter = Mock()

    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = []  # Default to empty list

    yield mock_session
    mock_session.close()


@pytest.fixture
def mock_wfh_requests():
    """Create mock WFH requests."""
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    return [
        Mock(
            arrangement_id=Mock(value=1),
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            wfh_date=tomorrow.strftime("%Y-%m-%d"),
        ),
        Mock(
            arrangement_id=Mock(value=2),
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            wfh_date=tomorrow.strftime("%Y-%m-%d"),
        ),
    ]


@pytest.mark.asyncio
async def test_auto_reject_old_requests(mock_db, mock_wfh_requests):
    """Test the auto-rejection of old requests."""

    # Set up the mock database to return the mock WFH requests
    mock_db.query.return_value.filter.return_value.all.return_value = mock_wfh_requests

    # Mock the update arrangement approval status function
    with patch(
        "src.arrangements.services.update_arrangement_approval_status", new_callable=AsyncMock
    ) as mock_update:
        # Ensure get_db returns the mock_db when called
        with patch("src.arrangements.scheduler.get_db", return_value=mock_db):
            await auto_reject_old_requests()

            # Check if the service was called for each request
            assert mock_update.call_count == len(mock_wfh_requests)

            # Verify the commit was called once after processing the requests
            mock_db.commit.assert_called_once()

            # Ensure that the rollback is not called
            mock_db.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_process_single_request(mock_db):
    """Test processing a single WFH request."""
    request = Mock(
        arrangement_id=Mock(value=1),
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        wfh_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
    )

    with patch(
        "src.arrangements.services.update_arrangement_approval_status", new_callable=AsyncMock
    ) as mock_update:
        success = await process_single_request(mock_db, request, system_approver_id=1)

        assert success
        assert mock_update.call_count == 1

        call_args = mock_update.call_args[1]
        assert call_args["db"] == mock_db
        assert call_args["wfh_update"].arrangement_id == request.arrangement_id.value
        assert call_args["wfh_update"].action == Action.REJECT


@pytest.mark.asyncio
async def test_auto_reject_no_requests(mock_db):
    """Test the scenario where there are no pending WFH requests."""
    # Setup the mock to return no requests
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with patch("src.arrangements.scheduler.get_db", return_value=mock_db):
        with patch("src.arrangements.scheduler.logger") as mock_logger:
            await auto_reject_old_requests()
            mock_logger.info.assert_called_with("No pending WFH requests found for auto-rejection")
            mock_db.commit.assert_not_called()
            mock_db.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_auto_reject_handles_error(mock_db, mock_wfh_requests):
    """Test error handling in auto-reject process."""
    mock_db.query.return_value.filter.return_value.all.return_value = mock_wfh_requests

    with patch(
        "src.arrangements.services.update_arrangement_approval_status", new_callable=AsyncMock
    ) as mock_update:
        mock_update.side_effect = Exception("Service error")

        with patch("src.arrangements.scheduler.get_db", return_value=mock_db):
            await auto_reject_old_requests()

        # Ensure rollback is called due to exception
        mock_db.rollback.assert_called_once()


def test_scheduler_startup_shutdown(test_client):
    """Test that the scheduler starts and shuts down correctly."""
    with patch("src.arrangements.scheduler.scheduler") as mock_scheduler:
        # Trigger lifespan to start the scheduler
        test_client.get("/")

        # Verify scheduler was started
        mock_scheduler.start.assert_called_once()

        # Close the client to trigger shutdown
        test_client.close()

        # Verify scheduler was shutdown
        mock_scheduler.shutdown.assert_called_once_with(wait=True)


if __name__ == "__main__":
    pytest.main(["-v"])
