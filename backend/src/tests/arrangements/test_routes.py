from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from src.app import app
from src.tests.test_utils import mock_db_session  # noqa: F401, E261

from backend.src.arrangements.archive.old_schemas import ArrangementResponse

client = TestClient(app)


class TestGetArrangementById:
    @patch("src.arrangements.services.get_arrangement_by_id")
    def test_success(self, mock_get_arrangement):
        # Arrange
        arrangement_id = 1

        mock_arrangement = MagicMock(spec=ArrangementResponse)
        mock_arrangement_data = {
            "arrangement_id": arrangement_id,
            "wfh_date": datetime.now().date(),
            "update_datetime": datetime.now(),
        }
        mock_arrangement.configure_mock(**mock_arrangement_data)

        mock_get_arrangement.return_value = mock_arrangement

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "message": "Arrangement retrieved successfully",
            "data": mock_arrangement_data,
        }
