from datetime import datetime
from unittest import mock
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from src.employees.models import DelegationStatus
from src.app import app
from src.employees.schemas import DelegateLogCreate
from src.employees.services import DelegationApprovalStatus

client = TestClient(app)


class TestDelegateManagerRoute:
    @patch("src.employees.services.delegate_manager")
    async def test_delegate_manager_success(self, mock_delegate_manager):
        # Arrange
        staff_id = 1
        delegate_manager_id = 2
        mock_delegate_log = MagicMock(spec=DelegateLogCreate)
        mock_delegate_log.manager_id = staff_id
        mock_delegate_log.delegate_manager_id = delegate_manager_id
        mock_delegate_log.date_of_delegation = datetime.now()
        mock_delegate_log.status_of_delegation = DelegationStatus.pending
        mock_delegate_log.model_dump.return_value = {
            "manager_id": staff_id,
            "delegate_manager_id": delegate_manager_id,
            "date_of_delegation": mock_delegate_log.date_of_delegation.isoformat(),
            "status_of_delegation": mock_delegate_log.status_of_delegation.value
        }
        mock_delegate_manager.return_value = mock_delegate_log

        # Act
        response = client.post(
            f"/employees/manager/delegate/{staff_id}?delegate_manager_id={delegate_manager_id}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegate_log.model_dump()

    @patch("src.employees.services.delegate_manager")
    async def test_delegate_manager_failure(self, mock_delegate_manager):
        # Arrange
        staff_id = 1
        delegate_manager_id = 2
        error_message = "Existing delegation error"
        mock_delegate_manager.return_value = error_message

        # Act
        response = client.post(
            f"/employees/manager/delegate/{staff_id}?delegate_manager_id={delegate_manager_id}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == error_message


class TestUpdateDelegationStatusRoute:
    @patch("src.employees.services.process_delegation_status")
    async def test_update_delegation_status_success(self, mock_process_status):
        # Arrange
        staff_id = 1
        status = DelegationApprovalStatus.accept
        description = "Approved delegation"
        mock_delegate_log = MagicMock(spec=DelegateLogCreate)
        mock_delegate_log.manager_id = staff_id
        mock_delegate_log.delegate_manager_id = 2
        mock_delegate_log.date_of_delegation = datetime.now()
        mock_delegate_log.status_of_delegation = DelegationStatus.accepted
        mock_delegate_log.model_dump.return_value = {
            "manager_id": staff_id,
            "delegate_manager_id": 2,
            "date_of_delegation": mock_delegate_log.date_of_delegation.isoformat(),
            "status_of_delegation": mock_delegate_log.status_of_delegation.value
        }
        mock_process_status.return_value = mock_delegate_log

        # Act
        response = client.put(
            f"/employees/manager/delegate/{staff_id}/status",
            params={"status": status.value},
            data={"description": description},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegate_log.model_dump()

    @patch("src.employees.services.process_delegation_status")
    async def test_update_delegation_status_reject_without_comment(self, mock_process_status):
        # Act
        response = client.put(
            f"/employees/manager/delegate/1/status",
            params={"status": DelegationApprovalStatus.reject.value},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Comment is required for rejected status."

    @patch("src.employees.services.process_delegation_status")
    async def test_update_delegation_status_not_found(self, mock_process_status):
        # Arrange
        staff_id = 1
        status = DelegationApprovalStatus.reject
        mock_process_status.return_value = "Delegation not found"

        # Act
        response = client.put(
            f"/employees/manager/delegate/{staff_id}/status",
            params={"status": status.value},
            data={"description": "Rejection reason"},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Delegation not found"


class TestUndelegateManagerRoute:
    @patch("src.employees.services.undelegate_manager")
    async def test_undelegate_manager_success(self, mock_undelegate_manager):
        # Arrange
        staff_id = 1
        mock_delegate_log = MagicMock(spec=DelegateLogCreate)
        mock_delegate_log.manager_id = staff_id
        mock_delegate_log.delegate_manager_id = 2
        mock_delegate_log.date_of_delegation = datetime.now()
        mock_delegate_log.status_of_delegation = DelegationStatus.undelegated
        mock_delegate_log.model_dump.return_value = {
            "manager_id": staff_id,
            "delegate_manager_id": 2,
            "date_of_delegation": mock_delegate_log.date_of_delegation.isoformat(),
            "status_of_delegation": mock_delegate_log.status_of_delegation.value
        }
        mock_undelegate_manager.return_value = mock_delegate_log

        # Act
        response = client.put(f"/employees/manager/undelegate/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegate_log.model_dump()


class TestViewDelegationsRoute:
    @patch("src.employees.services.view_delegations")
    def test_view_delegations_success(self, mock_view_delegations):
        # Arrange
        staff_id = 1
        mock_delegations = [{"staff_id": staff_id, "delegate_manager_id": 2, "status": "pending"}]
        mock_view_delegations.return_value = mock_delegations

        # Act
        response = client.get(f"/employees/manager/viewdelegations/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegations

    @patch("src.employees.services.view_delegations")
    def test_view_delegations_failure(self, mock_view_delegations):
        # Arrange
        staff_id = 1
        mock_view_delegations.side_effect = Exception("Unexpected error")

        # Act
        response = client.get(f"/employees/manager/viewdelegations/{staff_id}")

        # Assert
        assert response.status_code == 500
        assert (
            response.json()["detail"] == "An unexpected error occurred while fetching delegations."
        )


class TestViewAllDelegationsRoute:
    @patch("src.employees.services.view_all_delegations")
    def test_view_all_delegations_success(self, mock_view_all_delegations):
        # Arrange
        staff_id = 1
        mock_delegations = {
            "sent_delegations": [
                {"staff_id": staff_id, "delegate_manager_id": 2, "status": "accepted"}
            ],
            "received_delegations": [
                {"staff_id": staff_id, "delegate_manager_id": 3, "status": "pending"}
            ],
        }
        mock_view_all_delegations.return_value = mock_delegations

        # Act
        response = client.get(f"/employees/manager/viewalldelegations/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegations

    @patch("src.employees.services.view_all_delegations")
    def test_view_all_delegations_failure(self, mock_view_all_delegations):
        # Arrange
        staff_id = 1
        mock_view_all_delegations.side_effect = Exception("Unexpected error")

        # Act
        response = client.get(f"/employees/manager/viewalldelegations/{staff_id}")

        # Assert
        assert response.status_code == 500
        assert (
            response.json()["detail"] == "An unexpected error occurred while fetching delegations."
        )
