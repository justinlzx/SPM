from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest
from src.arrangements.services import (
    get_arrangement_by_id,
    get_personal_arrangements_by_filter,
    get_subordinates_arrangements,
    get_team_arrangements,
    create_arrangements_from_request,
    expand_recurring_arrangement,
    update_arrangement_approval_status,
)
from src.arrangements import models as arrangement_models
from src.arrangements import exceptions as arrangement_exceptions
from src.tests.test_utils import mock_db_session
from src.arrangements.schemas import ArrangementCreateWithFile, ArrangementUpdate
from fastapi.testclient import TestClient
from src.app import app
from moto import mock_aws
from src.employees.models import Employee
from src.tests.test_utils import mock_db_session
import httpx
from src.employees import exceptions as employee_exceptions
from src.arrangements.services import STATUS


client = TestClient(app)


@pytest.fixture
def mock_employee():
    return Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Doe",
        email="jane.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=None,
    )


def test_get_arrangement_by_id_success(mock_db_session):
    mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
        result = get_arrangement_by_id(mock_db_session, arrangement_id=1)
        assert result == mock_arrangement


def test_get_arrangement_by_id_not_found(mock_db_session):
    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=None):
        with pytest.raises(arrangement_exceptions.ArrangementNotFoundError):
            get_arrangement_by_id(mock_db_session, arrangement_id=1)


def test_get_personal_arrangements_by_filter_success(mock_db_session):
    mock_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]
    with patch("src.arrangements.crud.get_arrangements_by_filter", return_value=mock_arrangements):
        with patch(
            "src.utils.convert_model_to_pydantic_schema", return_value=["arrangement_schema"]
        ):
            result = get_personal_arrangements_by_filter(
                mock_db_session, staff_id=1, current_approval_status=[]
            )
            assert result == ["arrangement_schema"]


def test_get_personal_arrangements_by_filter_empty(mock_db_session):
    with patch("src.arrangements.crud.get_arrangements_by_filter", return_value=[]):
        result = get_personal_arrangements_by_filter(
            mock_db_session, staff_id=1, current_approval_status=[]
        )
        assert result == []


def test_get_subordinates_arrangements_success(mock_db_session):
    mock_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]
    with patch(
        "src.arrangements.crud.get_arrangements_by_staff_ids", return_value=mock_arrangements
    ):
        with patch(
            "src.utils.convert_model_to_pydantic_schema", return_value=["arrangement_schema"]
        ):
            result = get_subordinates_arrangements(
                mock_db_session, manager_id=1, current_approval_status=[]
            )
            assert result == ["arrangement_schema"]


def test_get_team_arrangements_success(mock_db_session):
    mock_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]
    with patch(
        "src.arrangements.crud.get_arrangements_by_staff_ids", return_value=mock_arrangements
    ):
        with patch(
            "src.utils.convert_model_to_pydantic_schema", return_value=["arrangement_schema"]
        ):
            result = get_team_arrangements(mock_db_session, staff_id=1, current_approval_status=[])
            assert isinstance(result, dict)
            assert "peers" in result


@pytest.mark.asyncio
async def test_create_arrangements_from_request_failure(mock_db_session):
    with patch("src.arrangements.crud.create_arrangements", side_effect=Exception("Failed")):
        with pytest.raises(Exception):
            await create_arrangements_from_request(mock_db_session, MagicMock(), [])


@pytest.mark.asyncio
async def test_create_arrangements_with_file_upload_success(mock_db_session, mock_employee):
    data = {
        "requester_staff_id": "1",
        "wfh_date": "2024-10-12",
        "wfh_type": "full",
        "reason_description": "Work from home request",
        "is_recurring": "false",
    }

    file_content = b"this is a test file"
    files = {"supporting_docs": ("test_file.pdf", file_content, "application/pdf")}

    mock_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]

    # Mock the database session
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_employee

    # Mock the httpx.AsyncClient.get method
    async def mock_get(*args, **kwargs):
        return httpx.Response(200, json={"manager_id": 2})

    # Mock the upload_file function
    async def mock_upload_file(*args, **kwargs):
        return {"file_url": "https://s3-bucket/test_file.pdf"}

    with patch("src.arrangements.crud.create_arrangements", return_value=mock_arrangements):
        with patch(
            "src.utils.convert_model_to_pydantic_schema", return_value=["arrangement_schema"]
        ):
            with patch("httpx.AsyncClient.get", side_effect=mock_get):
                with patch(
                    "src.employees.crud.get_employee_by_staff_id", return_value=mock_employee
                ):
                    with mock_aws():
                        with patch(
                            "src.arrangements.utils.upload_file", side_effect=mock_upload_file
                        ):
                            with patch("src.arrangements.services.boto3.client"):
                                with patch("src.database.SessionLocal", return_value=mock_db):
                                    with patch("sqlalchemy.orm.session.Session", mock_db):
                                        response = client.post(
                                            "/arrangements/request",
                                            data=data,
                                            files=files,
                                        )

    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1
    assert response_data[0] == "arrangement_schema"


def create_mock_arrangement_create_with_file(**kwargs):
    default_data = {
        "staff_id": 1,
        "wfh_date": "2024-01-01",
        "wfh_type": "full",
        "reason_description": "Work from home request",
        "is_recurring": False,
        "approving_officer": None,
        "update_datetime": datetime.now(),
        "current_approval_status": "pending",
        "supporting_doc_1": None,
        "supporting_doc_2": None,
        "supporting_doc_3": None,
    }
    default_data.update(kwargs)
    return ArrangementCreateWithFile(**default_data)


def test_expand_recurring_arrangement():
    wfh_request = create_mock_arrangement_create_with_file(
        is_recurring=True,
        recurring_frequency_unit="week",
        recurring_frequency_number=1,
        recurring_occurrences=3,
    )
    batch_id = 1
    result = expand_recurring_arrangement(wfh_request, batch_id)
    assert len(result) == 3
    assert result[0].wfh_date == "2024-01-01"
    assert result[1].wfh_date == "2024-01-08"
    assert result[2].wfh_date == "2024-01-15"
    assert all(arr.batch_id == batch_id for arr in result)


def test_expand_recurring_arrangement_monthly():
    wfh_request = create_mock_arrangement_create_with_file(
        is_recurring=True,
        recurring_frequency_unit="month",
        recurring_frequency_number=1,
        recurring_occurrences=3,
    )
    batch_id = 1
    result = expand_recurring_arrangement(wfh_request, batch_id)
    assert len(result) == 3
    assert result[0].wfh_date == "2024-01-01"
    assert result[1].wfh_date == "2024-02-01"
    assert result[2].wfh_date == "2024-03-01"
    assert all(arr.batch_id == batch_id for arr in result)


def test_update_arrangement_approval_status(mock_db_session):
    mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
    mock_arrangement.arrangement_id = 1

    wfh_update = ArrangementUpdate(
        arrangement_id=1,
        action="approve",
        approving_officer=2,
        reason_description="Approved by manager",
    )

    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
        with patch(
            "src.arrangements.crud.update_arrangement_approval_status",
            return_value=mock_arrangement,
        ):
            result = update_arrangement_approval_status(mock_db_session, wfh_update)

            assert result.arrangement_id == 1
            assert result.current_approval_status == "approved"
            assert result.approving_officer == 2
            assert result.reason_description == "Approved by manager"


@pytest.mark.asyncio
async def test_update_arrangement_approval_status_not_found(mock_db_session):
    wfh_update = ArrangementUpdate(
        arrangement_id=1,
        action="approve",
        approving_officer=2,
        reason_description="Approved by manager",
    )

    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=None):
        with pytest.raises(arrangement_exceptions.ArrangementNotFoundError):
            await update_arrangement_approval_status(mock_db_session, wfh_update)


@pytest.mark.asyncio
async def test_create_arrangements_from_request_recurring(mock_db_session, mock_employee):
    wfh_request = create_mock_arrangement_create_with_file(
        is_recurring=True,
        recurring_frequency_unit="week",
        recurring_frequency_number=1,
        recurring_occurrences=3,
    )

    mock_batch = MagicMock(spec=arrangement_models.RecurringRequest)
    mock_batch.batch_id = 1

    with patch("src.arrangements.crud.create_recurring_request", return_value=mock_batch):
        with patch(
            "src.arrangements.services.expand_recurring_arrangement",
            return_value=[wfh_request, wfh_request, wfh_request],
        ):
            with patch(
                "src.arrangements.crud.create_arrangements",
                return_value=[MagicMock(spec=arrangement_models.LatestArrangement)],
            ):
                with patch(
                    "src.utils.convert_model_to_pydantic_schema",
                    return_value=["arrangement_schema"],
                ):
                    with patch(
                        "src.employees.crud.get_employee_by_staff_id", return_value=mock_employee
                    ):
                        with patch(
                            "src.arrangements.services.fetch_manager_info",
                            return_value={"manager_id": 2},
                        ):
                            with patch("src.arrangements.services.boto3.client"):
                                with patch(
                                    "src.arrangements.utils.upload_file",
                                    return_value={"file_url": "https://example.com/file.pdf"},
                                ):
                                    result = await create_arrangements_from_request(
                                        mock_db_session, wfh_request, []
                                    )
                                    assert len(result) == 1
                                    assert result[0] == "arrangement_schema"


@pytest.mark.asyncio
async def test_create_arrangements_from_request_jack_sim(mock_db_session, mock_employee):
    wfh_request = create_mock_arrangement_create_with_file(staff_id=130002)

    with patch(
        "src.arrangements.crud.create_arrangements",
        return_value=[MagicMock(spec=arrangement_models.LatestArrangement)],
    ):
        with patch(
            "src.utils.convert_model_to_pydantic_schema", return_value=["arrangement_schema"]
        ):
            with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
                with patch(
                    "src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}
                ):
                    with patch("src.arrangements.services.boto3.client"):
                        with patch(
                            "src.arrangements.utils.upload_file",
                            return_value={"file_url": "https://example.com/file.pdf"},
                        ):
                            result = await create_arrangements_from_request(
                                mock_db_session, wfh_request, []
                            )
                            assert len(result) == 1
                            assert result[0] == "arrangement_schema"
                            assert wfh_request.current_approval_status == "approved"


@pytest.mark.asyncio
async def test_create_arrangements_from_request_file_upload_failure(mock_db_session, mock_employee):
    wfh_request = create_mock_arrangement_create_with_file()

    mock_file = MagicMock()

    with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
        with patch("src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}):
            with patch("src.arrangements.services.boto3.client"):
                with patch(
                    "src.arrangements.utils.upload_file", side_effect=Exception("Upload failed")
                ):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_arrangements_from_request(
                            mock_db_session, wfh_request, [mock_file]
                        )
                    assert exc_info.value.status_code == 500
                    assert "Error uploading files" in str(exc_info.value.detail)


def test_get_subordinates_arrangements_no_subordinates(mock_db_session):
    with patch("src.employees.services.get_subordinates_by_manager_id", return_value=[]):
        with pytest.raises(employee_exceptions.ManagerNotFoundException):
            get_subordinates_arrangements(mock_db_session, manager_id=1, current_approval_status=[])


def test_get_team_arrangements_employee_is_manager(mock_db_session):
    mock_peer_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]
    mock_subordinate_arrangements = [MagicMock(spec=arrangement_models.LatestArrangement)]

    with patch(
        "src.employees.services.get_peers_by_staff_id", return_value=[MagicMock(spec=Employee)]
    ):
        with patch(
            "src.arrangements.crud.get_arrangements_by_staff_ids",
            side_effect=[mock_peer_arrangements, mock_subordinate_arrangements],
        ):
            with patch("src.utils.convert_model_to_pydantic_schema", return_value=["schema"]):
                with patch(
                    "src.employees.services.get_subordinates_by_manager_id",
                    return_value=[MagicMock(spec=Employee)],
                ):
                    result = get_team_arrangements(
                        mock_db_session, staff_id=1, current_approval_status=[]
                    )
                    assert isinstance(result, dict)
                    assert "peers" in result
                    assert "subordinates" in result
                    assert result["peers"] == ["schema"]
                    assert result["subordinates"] == ["schema"]


@pytest.mark.parametrize(
    "action, expected_status",
    [
        ("approve", "approved"),
        ("reject", "rejected"),
        ("withdraw", "withdrawn"),
        ("cancel", "cancelled"),
    ],
)
def test_update_arrangement_approval_status_actions(mock_db_session, action, expected_status):
    mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
    mock_arrangement.arrangement_id = 1

    wfh_update = ArrangementUpdate(
        arrangement_id=1,
        action=action,
        approving_officer=2,
        reason_description="Action taken",
    )

    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
        with patch(
            "src.arrangements.crud.update_arrangement_approval_status",
            return_value=mock_arrangement,
        ):
            result = update_arrangement_approval_status(mock_db_session, wfh_update)

            assert result.arrangement_id == 1
            assert result.current_approval_status == expected_status
            assert result.approving_officer == 2
            assert result.reason_description == "Action taken"


def test_update_arrangement_approval_status_invalid_action(mock_db_session):
    mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
    mock_arrangement.arrangement_id = 1

    wfh_update = ArrangementUpdate(
        arrangement_id=1,
        action="approve",  # Use a valid action
        approving_officer=2,
        reason_description="Invalid action test",
    )

    with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
        with patch.dict(STATUS, {"approve": None}):  # Make 'approve' action invalid
            with pytest.raises(ValueError, match="Invalid action: approve"):
                update_arrangement_approval_status(mock_db_session, wfh_update)


@pytest.mark.asyncio
async def test_create_arrangements_from_request_file_upload_failure(mock_db_session, mock_employee):
    wfh_request = create_mock_arrangement_create_with_file()
    mock_file = MagicMock()

    with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
        with patch("src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}):
            with patch("src.arrangements.services.boto3.client"):
                with patch(
                    "src.arrangements.utils.upload_file", side_effect=Exception("Upload failed")
                ):
                    with patch("src.arrangements.utils.delete_file"):
                        with pytest.raises(HTTPException) as exc_info:
                            await create_arrangements_from_request(
                                mock_db_session, wfh_request, [mock_file]
                            )
                        assert exc_info.value.status_code == 500
                        assert "Error uploading files" in str(exc_info.value.detail)


def test_expand_recurring_arrangement_jack_sim():
    wfh_request = create_mock_arrangement_create_with_file(
        staff_id=130002,
        is_recurring=True,
        recurring_frequency_unit="week",
        recurring_frequency_number=1,
        recurring_occurrences=3,
    )
    batch_id = 1
    result = expand_recurring_arrangement(wfh_request, batch_id)
    assert len(result) == 3
    assert all(arr.current_approval_status == "approved" for arr in result)
    assert all(arr.batch_id == batch_id for arr in result)
