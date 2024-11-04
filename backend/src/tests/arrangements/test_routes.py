from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from src.app import app
from src.arrangements.commons import dataclasses as dc
from src.arrangements.commons.exceptions import ArrangementNotFoundException
from src.schemas import JSendResponse
from src.tests.test_utils import mock_db_session  # noqa: F401, E261

client = TestClient(app)


class TestGetArrangementById:
    @patch("src.arrangements.commons.schemas.ArrangementResponse")
    @patch("src.arrangements.routes.asdict")
    @patch("src.arrangements.services.get_arrangement_by_id")
    def test_success(self, mock_get_arrangement, mock_asdict, mock_pydantic):
        # Arrange
        arrangement_id = 1

        mock_arrangement_data = {
            "arrangement_id": arrangement_id,
            "wfh_date": datetime.now().date(),
            "update_datetime": datetime.now(),
        }

        mock_arrangement = MagicMock(spec=dc.ArrangementResponse)
        mock_arrangement.configure_mock(**mock_arrangement_data)
        mock_get_arrangement.return_value = mock_arrangement

        mock_asdict.return_value = mock_arrangement_data
        mock_pydantic.return_value = MagicMock()

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == JSendResponse(status="success", data=[]).model_dump()

    @patch("src.arrangements.services.get_arrangement_by_id")
    def test_failure_not_found(self, mock_get_arrangement):
        # Arrange
        arrangement_id = 1
        mock_get_arrangement.side_effect = ArrangementNotFoundException(arrangement_id)

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 404

    @patch("src.arrangements.services.get_arrangement_by_id")
    def test_failure_sqlalchemy(self, mock_get_arrangement):
        # Arrange
        arrangement_id = 1
        mock_get_arrangement.side_effect = SQLAlchemyError()

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 500


class TestGetPersonalArrangements:
    @patch("src.arrangements.commons.schemas.ArrangementResponse")
    @patch("src.arrangements.routes.asdict")
    @patch("src.arrangements.services.get_personal_arrangements")
    def test_success(self, mock_get_personal_arrangements, mock_asdict, mock_pydantic):
        # Arrange
        user_id = 1

        mock_arrangement_data = {
            "arrangement_id": 1,
            "wfh_date": datetime.now().date(),
            "update_datetime": datetime.now(),
        }

        mock_arrangement = MagicMock(spec=dc.ArrangementResponse)
        mock_arrangement.configure_mock(**mock_arrangement_data)
        mock_get_personal_arrangements.return_value = [mock_arrangement]

        mock_asdict.return_value = mock_arrangement_data
        mock_pydantic.return_value = MagicMock()

        # Act
        response = client.get(f"/arrangements/personal/{user_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == JSendResponse(status="success", data=[[]]).model_dump()

    @patch("src.arrangements.services.get_personal_arrangements")
    def test_failure_sqlalchemy(self, mock_get_personal_arrangements):
        # Arrange
        user_id = 1
        mock_get_personal_arrangements.side_effect = SQLAlchemyError()

        # Act
        response = client.get(f"/arrangements/personal/{user_id}")

        # Assert
        assert response.status_code == 500


class TestGetSubordinatesArrangements:
    @pytest.mark.parametrize(
        "group_by_date",
        [True, False],
    )
    @patch("src.arrangements.routes.PaginationMeta.model_validate")
    @patch("src.arrangements.routes.format_arrangements_response")
    @patch("src.arrangements.services.get_subordinates_arrangements")
    @patch("src.arrangements.commons.dataclasses.PaginationConfig.from_dict")
    @patch("src.arrangements.commons.dataclasses.ArrangementFilters.from_dict")
    def test_success(
        self,
        mock_filters_from_dict,
        mock_pagination_from_dict,
        mock_get_subordinates_arrangements,
        mock_format_response,
        mock_pagination_validate,
        group_by_date,
    ):
        # Arrange
        manager_id = 1
        mock_filters_from_dict.return_value = MagicMock(spec=dc.ArrangementFilters)
        mock_pagination_from_dict.return_value = MagicMock(spec=dc.PaginationConfig)
        mock_pagination_meta_dc = MagicMock(spec=dc.PaginationMeta)
        mock_pagination_meta_dc.total_count = 1

        mock_get_subordinates_arrangements.return_value = [
            [MagicMock(spec=dc.ArrangementResponse)] * 2
        ], mock_pagination_meta_dc

        if group_by_date:
            mock_format_response.return_value = [
                {
                    "date": "2021-01-01",
                    "pending_arrangements": [],
                }
            ]
        else:
            mock_format_response.return_value = []

        mock_pagination_validate.return_value = MagicMock()

        # Act
        response = client.get(
            f"/arrangements/subordinates/{manager_id}", params={"group_by_date": group_by_date}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "data" in response.json()
        assert "pagination_meta" in response.json()

    # @patch("src.arrangements.services.get_subordinates_arrangements")
    # def test_failure_sqlalchemy(self, mock_get_subordinate_arrangements):
    #     # Arrange
    #     user_id = 1
    #     mock_get_subordinate_arrangements.side_effect = SQLAlchemyError()

    #     # Act
    #     response = client.get(f"/arrangements/subordinate/{user_id}")

    #     # Assert
    #     assert response.status_code == 500


class TestGetTeamArrangements:
    @pytest.mark.parametrize(
        "group_by_date",
        [True, False],
    )
    @patch("src.arrangements.routes.PaginationMeta.model_validate")
    @patch("src.arrangements.routes.format_arrangements_response")
    @patch("src.arrangements.services.get_team_arrangements")
    @patch("src.arrangements.commons.dataclasses.PaginationConfig.from_dict")
    @patch("src.arrangements.commons.dataclasses.ArrangementFilters.from_dict")
    def test_success(
        self,
        mock_filters_from_dict,
        mock_pagination_from_dict,
        mock_get_team_arrangements,
        mock_format_response,
        mock_pagination_validate,
        group_by_date,
    ):
        # Arrange
        staff_id = 1
        mock_filters_from_dict.return_value = MagicMock(spec=dc.ArrangementFilters)
        mock_pagination_from_dict.return_value = MagicMock(spec=dc.PaginationConfig)
        mock_pagination_meta_dc = MagicMock(spec=dc.PaginationMeta)
        mock_pagination_meta_dc.total_count = 1

        mock_get_team_arrangements.return_value = [
            [MagicMock(spec=dc.ArrangementResponse)] * 2
        ], mock_pagination_meta_dc

        if group_by_date:
            mock_format_response.return_value = [
                {
                    "date": "2021-01-01",
                    "pending_arrangements": [],
                }
            ]
        else:
            mock_format_response.return_value = []

        mock_pagination_validate.return_value = MagicMock()

        # Act
        response = client.get(
            f"/arrangements/team/{staff_id}", params={"group_by_date": group_by_date}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "data" in response.json()
        assert "pagination_meta" in response.json()


class TestGetArrangementLogs:
    @patch("src.arrangements.commons.schemas.ArrangementLogResponse")
    @patch("src.arrangements.routes.asdict")
    @patch("src.arrangements.services.get_arrangement_logs")
    def test_success(self, mock_get_logs, mock_asdict, mock_pydantic):
        # Arrange
        num_logs = 3
        mock_get_logs.return_value = [MagicMock(spec=dc.ArrangementLogResponse)] * num_logs
        mock_asdict.return_value = MagicMock()
        mock_pydantic.return_value = MagicMock()

        # Act
        result = client.get("/arrangements/logs/all")

        # Assert
        assert result.status_code == 200
        assert result.json() == JSendResponse(status="success", data=[[]] * num_logs).model_dump()

        mock_asdict.assert_called()
        assert mock_asdict.call_count == num_logs

        mock_pydantic.assert_called()
        assert mock_pydantic.call_count == num_logs


class TestCreateWfhRequest:
    @patch("src.arrangements.routes.format_arrangements_response")
    @patch("src.arrangements.services.create_arrangements_from_request")
    def test_success(self, mock_create_arrangements, mock_format_response):
        # Act
        result = client.post("/arrangements/create", json={})

        # Assert
        assert result.status_code == 200
        assert "data" in result.json()


class TestUpdateWfhRequest:
    @patch("src.arrangements.routes.format_arrangement_response")
    @patch("src.arrangements.services.update_arrangement_approval_status")
    def test_success(self, mock_update_arrangement, mock_format_response):
        # Act
        result = client.put(
            "/arrangements/1/status",
            json={
                "action": "approve",
                "approving_officer": 1,
            },
        )

        # Assert
        print(result.json())
        assert result.status_code == 200
        assert "data" in result.json()
