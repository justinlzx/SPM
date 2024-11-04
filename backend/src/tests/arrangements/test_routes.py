from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.arrangements.commons import dataclasses as dc
from src.arrangements.commons.exceptions import ArrangementNotFoundException
from src.employees.exceptions import ManagerWithIDNotFoundException
from src.schemas import JSendResponse
from src.tests.test_utils import mock_db_session  # noqa: F401, E261

client = TestClient(app)


@pytest.fixture
def mock_filter_params():
    return {
        "current_approval_status": ["approved"],
        "name": "John Doe",
        "wfh_type": ["full"],
        "start_date": "2021-01-01",
        "end_date": "2021-01-31",
        "reason": "Test reason",
        "group_by_date": True,
        "department": "IT",
    }


@pytest.fixture
def mock_pagination_params():
    return {
        "items_per_page": 10,
        "page_num": 1,
    }


@patch("src.arrangements.services.get_all_arrangements")
@patch("src.arrangements.commons.dataclasses.ArrangementFilters.from_dict")
class TestGetArrangements:
    @patch("src.arrangements.routes.format_arrangements_response")
    def test_success(
        self,
        mock_format_response,
        mock_filters_from_dict,
        mock_get_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        mock_filters_from_dict.return_value = MagicMock(spec=dc.ArrangementFilters)
        mock_get_arrangements.return_value = [MagicMock(spec=dc.ArrangementResponse)] * 2
        mock_format_response.return_value = []

        # Act
        response = client.get(
            "/arrangements",
            params={**mock_filter_params, **mock_pagination_params},
        )

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()

    def test_failure_unknown(self, mock_filters_from_dict, mock_get_arrangements):
        # Arrange
        mock_filters_from_dict.return_value = MagicMock(spec=dc.ArrangementFilters)
        mock_get_arrangements.side_effect = Exception()

        # Act
        response = client.get("/arrangements")

        # Assert
        assert response.status_code == 500


@patch("src.arrangements.services.get_arrangement_by_id")
class TestGetArrangementById:
    @patch("src.arrangements.routes.format_arrangement_response")
    def test_success(self, mock_format_response, mock_get_arrangement):
        # Arrange
        arrangement_id = 1
        mock_get_arrangement.return_value = MagicMock(spec=dc.ArrangementResponse)
        mock_format_response.return_value = MagicMock()

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()

    def test_failure_not_found(self, mock_get_arrangement):
        # Arrange
        arrangement_id = 1
        mock_get_arrangement.side_effect = ArrangementNotFoundException(arrangement_id)

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 404

    def test_failure_unknown(self, mock_get_arrangement):
        # Arrange
        arrangement_id = 1
        mock_get_arrangement.side_effect = Exception()

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 500


@patch("src.arrangements.services.get_personal_arrangements")
class TestGetPersonalArrangements:
    @patch("src.arrangements.routes.format_arrangements_response")
    def test_success(self, mock_format_response, mock_get_personal_arrangements):
        # Arrange
        staff_id = 1

        # Act
        response = client.get(
            f"/arrangements/personal/{staff_id}",
            params={
                "current_approval_status": ["approved"],
            },
        )

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()

    def test_failure_unknown(self, mock_get_personal_arrangements):
        # Arrange
        staff_id = 1
        mock_get_personal_arrangements.side_effect = Exception()

        # Act
        response = client.get(f"/arrangements/personal/{staff_id}")

        # Assert
        assert response.status_code == 500


@patch("src.arrangements.services.get_subordinates_arrangements")
@patch("src.arrangements.commons.dataclasses.PaginationConfig.from_dict")
@patch("src.arrangements.commons.dataclasses.ArrangementFilters.from_dict")
class TestGetSubordinatesArrangements:
    @patch("src.arrangements.routes.PaginationMeta.model_validate")
    @patch("src.arrangements.routes.format_arrangements_response")
    def test_success(
        self,
        mock_format_response,
        mock_pagination_validate,
        mock_filters_from_dict,
        mock_pagination_from_dict,
        mock_get_subordinates_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        manager_id = 1
        mock_pagination_meta_dc = MagicMock(spec=dc.PaginationMeta)
        mock_pagination_meta_dc.total_count = 1

        mock_get_subordinates_arrangements.return_value = [
            [MagicMock(spec=dc.ArrangementResponse)] * 2
        ], mock_pagination_meta_dc

        # Act
        response = client.get(
            f"/arrangements/subordinates/{manager_id}",
            params={**mock_filter_params, **mock_pagination_params},
        )

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()
        assert "pagination_meta" in response.json()

    def test_failure_manager_not_found(
        self,
        mock_get_subordinates_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        manager_id = 1
        mock_get_subordinates_arrangements.side_effect = ManagerWithIDNotFoundException(manager_id)

        # Act
        response = client.get(f"/arrangements/subordinates/{manager_id}")

        # Assert
        assert response.status_code == 404

    def test_failure_unknown(
        self,
        mock_get_subordinates_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        manager_id = 1
        mock_get_subordinates_arrangements.side_effect = Exception()

        # Act
        response = client.get(f"/arrangements/subordinates/{manager_id}")

        # Assert
        assert response.status_code == 500


@patch("src.arrangements.services.get_team_arrangements")
@patch("src.arrangements.commons.dataclasses.PaginationConfig.from_dict")
@patch("src.arrangements.commons.dataclasses.ArrangementFilters.from_dict")
class TestGetTeamArrangements:
    @patch("src.arrangements.routes.PaginationMeta.model_validate")
    @patch("src.arrangements.routes.format_arrangements_response")
    def test_success(
        self,
        mock_format_response,
        mock_pagination_validate,
        mock_filters_from_dict,
        mock_pagination_from_dict,
        mock_get_team_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        staff_id = 1
        mock_pagination_meta_dc = MagicMock(spec=dc.PaginationMeta)
        mock_pagination_meta_dc.total_count = 1

        mock_get_team_arrangements.return_value = [
            [MagicMock(spec=dc.ArrangementResponse)] * 2
        ], mock_pagination_meta_dc

        # Act
        response = client.get(
            f"/arrangements/team/{staff_id}",
            params={**mock_filter_params, **mock_pagination_params},
        )

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()
        assert "pagination_meta" in response.json()

    def test_failure_unknown(
        self,
        mock_get_team_arrangements,
        mock_filter_params,
        mock_pagination_params,
    ):
        # Arrange
        staff_id = 1
        mock_get_team_arrangements.side_effect = Exception()

        # Act
        response = client.get(f"/arrangements/team/{staff_id}")

        # Assert
        assert response.status_code == 500


class TestGetArrangementLogs:
    @patch("src.arrangements.commons.schemas.ArrangementLogResponse.model_validate")
    @patch("src.arrangements.services.get_arrangement_logs")
    def test_success(self, mock_get_logs, mock_pydantic):
        # Arrange
        num_logs = 3
        mock_get_logs.return_value = [MagicMock(spec=dc.ArrangementLogResponse)] * num_logs
        mock_pydantic.return_value = MagicMock()

        # Act
        result = client.get("/arrangements/logs/all")

        # Assert
        assert result.status_code == 200
        assert result.json() == JSendResponse(status="success", data=[[]] * num_logs).model_dump()

        mock_pydantic.assert_called()
        assert mock_pydantic.call_count == num_logs


class TestCreateWfhRequest:
    @patch("src.arrangements.routes.format_arrangements_response")
    @patch("src.arrangements.services.create_arrangements_from_request")
    def test_success(self, mock_create_arrangements, mock_format_response):
        # Arrange
        files = [
            (
                "supporting_docs",
                ("dummy.pdf", open("src/tests/arrangements/dummy.pdf", "rb"), "application/pdf"),
            ),
            (
                "supporting_docs",
                ("dog.jpg", open("src/tests/arrangements/dog.jpg", "rb"), "image/jpeg"),
            ),
            (
                "supporting_docs",
                ("cat.png", open("src/tests/arrangements/cat.png", "rb"), "image/png"),
            ),
        ]
        try:
            # Act
            result = client.post(
                "/arrangements/request",
                data={
                    "requester_staff_id": 1,
                    "wfh_date": "2021-01-01",
                    "wfh_type": "full",
                    "is_recurring": True,
                    "reason_description": "Test reason",
                    "recurring_frequency_number": 1,
                    "recurring_frequency_unit": "week",
                    "recurring_occurrences": 3,
                },  # type: ignore
                files=files,
            )

            # Assert
            assert result.status_code == 200
            assert "data" in result.json()
        finally:
            for _, (filename, file, _) in files:
                file.close()


class TestUpdateWfhRequest:
    @patch("src.arrangements.routes.format_arrangement_response")
    @patch("src.arrangements.services.update_arrangement_approval_status")
    def test_success(self, mock_update_arrangement, mock_format_response):
        # Arrange
        files = [
            (
                "supporting_docs",
                ("dummy.pdf", open("src/tests/arrangements/dummy.pdf", "rb"), "application/pdf"),
            ),
            (
                "supporting_docs",
                ("dog.jpg", open("src/tests/arrangements/dog.jpg", "rb"), "image/jpeg"),
            ),
            (
                "supporting_docs",
                ("cat.png", open("src/tests/arrangements/cat.png", "rb"), "image/png"),
            ),
        ]

        try:
            # Act
            result = client.put(
                "/arrangements/1/status",
                data={
                    "action": "approve",
                    "approving_officer": 1,
                },  # type: ignore
                files=files,
            )

            # Assert
            assert result.status_code == 200
            assert "data" in result.json()
        finally:
            for _, (filename, file, _) in files:
                file.close()
