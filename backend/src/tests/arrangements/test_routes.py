from datetime import datetime
from typing import List
from unittest.mock import MagicMock, patch

import botocore
import botocore.exceptions
import httpx
import pytest
from fastapi import File
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from src.app import app
from src.arrangements import exceptions as arrangement_exceptions
from src.arrangements import models as arrangement_models
from src.arrangements.schemas import (
    ArrangementCreateResponse,
    ArrangementCreateWithFile,
    ArrangementResponse,
    ArrangementUpdate,
    ManagerPendingRequests,
)
from src.arrangements.services import (
    STATUS,
    create_arrangements_from_request,
    expand_recurring_arrangement,
    get_approving_officer,
    get_arrangement_by_id,
    get_personal_arrangements,
    get_subordinates_arrangements,
    get_team_arrangements,
    update_arrangement_approval_status,
)
from src.employees import exceptions as employee_exceptions
from src.employees.schemas import EmployeeBase
from src.tests.test_utils import mock_db_session  # noqa: F401, E261

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
        mock_arrangement_data["wfh_date"] = mock_arrangement_data["wfh_date"].isoformat()
        mock_arrangement_data["update_datetime"] = mock_arrangement_data[
            "update_datetime"
        ].isoformat()

        mock_get_arrangement.return_value = mock_arrangement
        
        print(mock_arrangement.model_dump())

        # Act
        response = client.get(f"/arrangements/{arrangement_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "message": "Arrangement retrieved successfully",
            "data": mock_arrangement_data,
        }
