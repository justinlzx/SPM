from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.employees.exceptions import EmployeeNotFoundException, ManagerNotFoundException
from src.employees.models import DelegationStatus
from src.app import app
from src.employees.schemas import DelegateLogCreate
from src.employees.services import DelegationApprovalStatus


client = TestClient(app)


def create_mock_employee():
    """Helper function to create a mock employee with all required fields"""
    return {
        "staff_id": 12345,
        "staff_fname": "John",
        "staff_lname": "Doe",
        "email": "john@example.com",
        "dept": "Engineering",
        "position": "Engineer",
        "country": "Singapore",
        "role": 1,
    }


class TestGetReportingManagerAndPeerEmployees:
    @patch("src.employees.services.get_manager_by_subordinate_id")
    def test_ceo_staff_id(self, mock_get_manager):
        # Arrange
        staff_id = 130002

        # Act
        response = client.get(f"/employees/manager/peermanager/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"manager_id": None, "peer_employees": []}
        mock_get_manager.assert_not_called()

    @patch("src.employees.services.get_manager_by_subordinate_id")
    def test_no_manager_found(self, mock_get_manager):
        # Arrange
        staff_id = 12345
        mock_get_manager.return_value = (None, [])

        # Act
        response = client.get(f"/employees/manager/peermanager/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"manager_id": None, "peer_employees": []}

    @patch("src.employees.services.get_manager_by_subordinate_id")
    @patch("src.utils.convert_model_to_pydantic_schema")
    def test_successful_retrieval(self, mock_convert, mock_get_manager):
        # Arrange
        staff_id = 12345
        mock_manager = MagicMock()
        mock_manager.staff_id = 67890
        mock_peers = [create_mock_employee()]
        mock_get_manager.return_value = (mock_manager, mock_peers)

        mock_peer_models = [create_mock_employee()]
        mock_convert.return_value = mock_peer_models

        # Act
        response = client.get(f"/employees/manager/peermanager/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["manager_id"] == 67890
        assert len(response.json()["peer_employees"]) > 0

    @patch("src.employees.services.get_manager_by_subordinate_id")
    def test_employee_not_found(self, mock_get_manager):
        # Arrange
        staff_id = 12345
        mock_get_manager.side_effect = EmployeeNotFoundException(staff_id)

        # Act
        response = client.get(f"/employees/manager/peermanager/{staff_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Employee with ID {staff_id} not found"

    @patch("src.employees.services.get_manager_by_subordinate_id")
    def test_manager_not_found(self, mock_get_manager):
        # Arrange
        staff_id = 12345
        mock_get_manager.side_effect = ManagerNotFoundException()

        # Act
        response = client.get(f"/employees/manager/peermanager/{staff_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Manager not found"


class TestGetEmployeeByStaffId:
    @patch("src.employees.services.get_employee_by_id")
    def test_successful_retrieval(self, mock_get_employee):
        # Arrange
        staff_id = 12345
        mock_employee = create_mock_employee()
        mock_get_employee.return_value = mock_employee

        # Act
        response = client.get(f"/employees/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["staff_id"] == staff_id

    @patch("src.employees.services.get_employee_by_id")
    def test_employee_not_found(self, mock_get_employee):
        # Arrange
        staff_id = 12345
        mock_get_employee.side_effect = EmployeeNotFoundException(staff_id)

        # Act
        response = client.get(f"/employees/{staff_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Employee with ID {staff_id} not found"


class TestGetEmployeeByEmail:
    @patch("src.employees.services.get_employee_by_email")
    def test_successful_retrieval(self, mock_get_employee):
        # Arrange
        email = "john@example.com"
        mock_employee = create_mock_employee()
        mock_get_employee.return_value = mock_employee

        # Act
        response = client.get(f"/employees/email/{email}")

        # Assert
        assert response.status_code == 200
        assert response.json()["email"] == email

    @patch("src.employees.services.get_employee_by_email")
    def test_employee_not_found(self, mock_get_employee):
        # Arrange
        email = "john@example.com"
        staff_id = None
        mock_get_employee.side_effect = EmployeeNotFoundException(staff_id)

        # Act
        response = client.get(f"/employees/email/{email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Employee with ID {staff_id} not found"


class TestGetSubordinatesByManagerId:
    @patch("src.employees.services.get_subordinates_by_manager_id")
    @patch("src.utils.convert_model_to_pydantic_schema")
    def test_successful_retrieval(self, mock_convert, mock_get_subordinates):
        # Arrange
        manager_id = 12345
        mock_employees = [create_mock_employee()]
        mock_get_subordinates.return_value = mock_employees
        mock_convert.return_value = mock_employees

        # Act
        response = client.get(f"/employees/manager/employees/{manager_id}")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) > 0
        assert response.json()[0]["staff_id"] == mock_employees[0]["staff_id"]

    @patch("src.employees.services.get_subordinates_by_manager_id")
    def test_manager_not_found(self, mock_get_subordinates):
        # Arrange
        manager_id = 12345
        mock_get_subordinates.side_effect = ManagerNotFoundException()

        # Act
        response = client.get(f"/employees/manager/employees/{manager_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Manager not found"


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
            "status_of_delegation": mock_delegate_log.status_of_delegation.value,
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
            "status_of_delegation": mock_delegate_log.status_of_delegation.value,
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
            "status_of_delegation": mock_delegate_log.status_of_delegation.value,
        }
        mock_undelegate_manager.return_value = mock_delegate_log

        # Act
        response = client.put(f"/employees/manager/undelegate/{staff_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == mock_delegate_log.model_dump()

    @patch("src.employees.services.undelegate_manager")
    async def test_undelegate_manager_not_found(self, mock_undelegate_manager):
        # Arrange
        staff_id = 1
        error_message = "Delegation not found"
        mock_undelegate_manager.return_value = error_message

        # Act
        response = client.put(f"/employees/manager/undelegate/{staff_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == error_message

    @patch("src.employees.services.undelegate_manager")
    async def test_undelegate_manager_other_error(self, mock_undelegate_manager):
        # Arrange
        staff_id = 1
        error_message = "Invalid delegation status"  # Any error message not containing "not found"
        mock_undelegate_manager.return_value = error_message

        # Act
        response = client.put(f"/employees/manager/undelegate/{staff_id}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == error_message


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
