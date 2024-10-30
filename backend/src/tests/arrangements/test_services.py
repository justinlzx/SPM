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

from backend.src.arrangements.archive.old_schemas import (
    ArrangementCreateResponse,
    ArrangementCreateWithFile,
    ArrangementResponse,
    ArrangementUpdate,
    ManagerPendingRequests,
)
from backend.src.arrangements.commons import exceptions as arrangement_exceptions
from backend.src.arrangements.commons import models as arrangement_models

client = TestClient(app)


@pytest.fixture
def mock_employee():
    return EmployeeBase(
        staff_id=123,
        staff_fname="John",
        staff_lname="Doe",
        email="john.doe@example.com",
        dept="IT",
        position="Developer",
        country="USA",
        role=1,
        reporting_manager=456,
    )


@pytest.fixture
def mock_manager():
    return EmployeeBase(
        staff_id=456,
        staff_fname="Michael",
        staff_lname="Scott",
        email="michael.scott@example.com",
        dept="Sales",
        position="Regional Manager",
        country="USA",
        role=1,
        reporting_manager=789,
    )


@pytest.fixture
def mock_s3_client():
    with patch("boto3.client") as mock_client:
        s3_client = MagicMock()
        mock_client.return_value = s3_client
        yield s3_client


@pytest.fixture
def mock_presigned_url():
    def _presigned_url(file_path):
        return f"https://example.com/presigned-url/{file_path}"

    return _presigned_url


@pytest.fixture
def mock_arrangement_data():
    return {
        "arrangement_id": 1,
        "requester_staff_id": 123,
        "wfh_date": "2024-10-12",
        "wfh_type": "full",
        "approving_officer": 456,
        "reason_description": "Work from home",
        "update_datetime": datetime.now(),
        "current_approval_status": "pending approval",
        "is_recurring": False,
        "recurring_end_date": None,
        "recurring_frequency_number": None,
        "recurring_frequency_unit": None,
        "recurring_occurrences": None,
        "batch_id": None,
        "supporting_doc_1": "test_file_1.pdf",
        "supporting_doc_2": None,
        "supporting_doc_3": None,
        "requester_info": {
            "staff_id": 123,
            "staff_fname": "John",
            "staff_lname": "Doe",
            "email": "john.doe@example.com",
            "dept": "IT",
            "position": "Developer",
            "country": "USA",
            "role": 1,
            "reporting_manager": 456,
        },
        "latest_log_id": 1,
    }


@pytest.fixture
def mock_db_arrangement(mock_arrangement_data):
    class MockDBArrangement:
        def __init__(self, data):
            self.__dict__.update(data)

    return MockDBArrangement(mock_arrangement_data)


@pytest.fixture
def mock_manager_pending_request_response(mock_arrangement_data):
    return {
        "date": "2024-10-12",
        "pending_arrangements": [mock_arrangement_data],
        "pagination_meta": {
            "total_items": 1,
            "total_pages": 1,
            "current_page": 1,
            "items_per_page": 10,
        },
    }


def create_mock_arrangement_create_with_file(**kwargs):
    default_data = {
        "staff_id": 1,
        "wfh_date": "2024-01-01",
        "wfh_type": "full",
        "reason_description": "Work from home request",
        "is_recurring": False,
        "approving_officer": None,
        "update_datetime": datetime.now(),
        "current_approval_status": "pending approval",
        "supporting_doc_1": None,
        "supporting_doc_2": None,
        "supporting_doc_3": None,
    }
    default_data.update(kwargs)
    return ArrangementCreateWithFile(**default_data)


# Mock the httpx.AsyncClient.get method
async def mock_get(*args, **kwargs):
    return httpx.Response(200, json={"manager_id": 2})


# Mock the upload_file function
# async def mock_upload_file(*args, **kwargs):
#     return {"file_url": "https://s3-bucket/test_file.pdf"}


class TestGetArrangementById:
    @patch("src.utils.convert_model_to_pydantic_schema")
    @patch("src.arrangements.crud.get_arrangement_by_id")
    def test_success(self, mock_get_arrangement, mock_convert, mock_db_session):
        # Arrange
        mock_get_arrangement.return_value = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_convert.return_value = [MagicMock(spec=ArrangementResponse)]

        # Act
        result = get_arrangement_by_id(mock_db_session, arrangement_id=1)

        # Assert
        # Verify the mocks were called correctly
        mock_get_arrangement.assert_called_once_with(mock_db_session, 1)
        mock_convert.assert_called_once_with(
            [mock_get_arrangement.return_value], ArrangementResponse
        )
        # Verify the result matches expected
        assert result == mock_convert.return_value[0]

        # # Set up the mock return values
        # mock_get_arrangement.return_value = mock_arrangement
        # expected_response = ArrangementResponse(**mock_arrangement_data)
        # mock_convert.return_value = expected_response

    @patch("src.arrangements.crud.get_arrangement_by_id")
    def test_not_found_failure(self, mock_get_arrangement, mock_db_session):
        mock_get_arrangement.return_value = None

        with pytest.raises(arrangement_exceptions.ArrangementNotFoundException):
            get_arrangement_by_id(mock_db_session, arrangement_id=1)


class TestGetPersonalArrangements:
    @patch("src.utils.convert_model_to_pydantic_schema")
    @patch("src.arrangements.crud.get_arrangements")
    @pytest.mark.parametrize(
        "current_approval_status",
        [
            None,
            ["pending approval"],
            ["approved"],
            ["rejected"],
            ["withdrawn"],
            ["cancelled"],
        ],
    )
    def test_success(
        self, mock_get_arrangements, mock_convert, current_approval_status, mock_db_session
    ):
        mock_get_arrangements.return_value = [MagicMock(spec=arrangement_models.LatestArrangement)]
        mock_convert.return_value = [MagicMock(spec=ArrangementResponse)]

        result = get_personal_arrangements(
            mock_db_session, staff_id=1, current_approval_status=current_approval_status
        )

        mock_get_arrangements.assert_called_once_with(mock_db_session, 1, current_approval_status)
        mock_convert.assert_called_once_with(
            mock_get_arrangements.return_value, ArrangementResponse
        )
        assert result == mock_convert.return_value

    @patch("src.arrangements.crud.get_arrangements")
    def test_empty_success(self, mock_get_arrangements, mock_db_session):
        mock_get_arrangements.return_value = []

        result = get_personal_arrangements(mock_db_session, staff_id=1, current_approval_status=[])

        assert result == []


class TestGetSubordinatesArrangements:
    # TODO: Combine with success with filters
    @patch("src.arrangements.services.group_arrangements_by_date")
    @patch("src.arrangements.services.create_presigned_url")
    @patch("src.utils.convert_model_to_pydantic_schema")
    @patch("src.arrangements.crud.get_arrangements")
    @patch("src.employees.services.get_subordinates_by_manager_id")
    @pytest.mark.parametrize(
        "supporting_docs",
        [
            ["/140002/2024-10-12T14:30:00/test_file_1.pdf", None, None],
            [
                "/140002/2024-10-12T14:30:00/test_file_1.pdf",
                "/140002/2024-10-12T14:30:00/test_file_2.pdf",
                "/1/2024-10-12T14:30:00/test_file_3.pdf",
            ],
        ],
    )
    def test_success_no_filters(
        self,
        mock_get_subordinates,
        mock_get_arrangements,
        mock_convert,
        mock_create_presigned_url,
        mock_group_arrangements,
        supporting_docs,
        mock_db_session,
        mock_presigned_url,
        mock_employee,
    ):
        # Arrange
        mock_get_subordinates.return_value = [mock_employee]

        mock_get_arrangements.return_value = [MagicMock(spec=arrangement_models.LatestArrangement)]

        mock_arrangement = MagicMock(spec=ArrangementCreateResponse)
        mock_arrangement.configure_mock(
            supporting_doc_1=supporting_docs[0],
            supporting_doc_2=supporting_docs[1],
            supporting_doc_3=supporting_docs[2],
        )

        mock_convert.return_value = [mock_arrangement]
        mock_create_presigned_url.side_effect = [mock_presigned_url(doc) for doc in supporting_docs]
        mock_group_arrangements.return_value = [MagicMock(spec=ManagerPendingRequests)]

        manager_id = 1
        items_per_page = 10
        page_num = 1
        # mock_arrangement = ArrangementCreateResponse(**mock_arrangement_data)
        # mock_arrangements = [mock_arrangement]

        # mock_get_subordinates.return_value = [mock_employee]
        # mock_get_arrangements.return_value = mock_arrangements
        # mock_create_presigned_url.side_effect = mock_presigned_url

        # Act
        result = get_subordinates_arrangements(
            mock_db_session,
            manager_id=manager_id,
            items_per_page=items_per_page,
            page_num=page_num,
        )

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2  # return data and pagination metadata

        arrangements, pagination_meta = result

        assert isinstance(arrangements, List)
        assert isinstance(arrangements[0], ManagerPendingRequests)
        assert isinstance(pagination_meta, dict)
        assert "total_count" in pagination_meta
        assert "page_size" in pagination_meta
        assert "page_num" in pagination_meta
        assert "total_pages" in pagination_meta
        assert pagination_meta["total_count"] == len(mock_group_arrangements.return_value)
        assert pagination_meta["page_size"] == items_per_page
        assert pagination_meta["page_num"] == page_num
        assert pagination_meta["total_pages"] == 1

    @patch("src.employees.crud.get_subordinates_by_manager_id")
    def test_no_subordinates(self, mock_get_subordinates, mock_db_session):
        manager_id = 1

        mock_get_subordinates.side_effect = employee_exceptions.ManagerWithIDNotFoundException(
            manager_id=manager_id
        )

        with pytest.raises(employee_exceptions.ManagerWithIDNotFoundException):
            get_subordinates_arrangements(mock_db_session, manager_id=manager_id)


class TestGetTeamArrangements:
    @patch("src.arrangements.services.get_subordinates_arrangements")
    @patch("src.utils.convert_model_to_pydantic_schema")
    @patch("src.arrangements.crud.get_arrangements")
    @patch("src.employees.services.get_peers_by_staff_id")
    def test_success(
        self,
        mock_db_session,
        mock_presigned_url,
        mock_arrangement_data,
        mock_employee,
        mock_manager_pending_request_response,
    ):
        mock_arrangements = ArrangementResponse(**mock_arrangement_data)
        # mock_arrangements.__dict__ =

        with patch("src.employees.services.get_peers_by_staff_id", return_value=[mock_employee]):
            with patch(
                "src.arrangements.crud.get_arrangements",
                return_value=[mock_arrangements],
            ):
                with patch(
                    "src.arrangements.services.get_subordinates_arrangements",
                    return_value=[mock_manager_pending_request_response],
                ):
                    with patch(
                        "src.employees.services.get_subordinates_by_manager_id",
                        return_value=[mock_employee],
                    ):
                        with patch(
                            "src.arrangements.services.create_presigned_url",
                            side_effect=mock_presigned_url,
                        ):
                            result = get_team_arrangements(
                                mock_db_session, staff_id=1, current_approval_status=[]
                            )

        assert isinstance(result, dict)
        assert "peers" in result
        assert "subordinates" in result
        assert len(result["peers"]) == 1
        assert len(result["subordinates"]) == 1
        assert (
            result["peers"][0].supporting_doc_1
            == "https://example.com/presigned-url/test_file_1.pdf"
        )
        assert (
            result["subordinates"][0].supporting_doc_1
            == "https://example.com/presigned-url/test_file_1.pdf"
        )

    def test_employee_is_manager(
        self,
        mock_db_session,
        mock_s3_client,
        mock_presigned_url,
        mock_db_arrangement,
        mock_employee,
    ):
        mock_db_arrangement.supporting_doc_2 = "test_file_2.pdf"
        mock_arrangements = [mock_db_arrangement]

        with patch("src.employees.services.get_peers_by_staff_id", return_value=[mock_employee]):
            with patch("src.arrangements.crud.get_arrangements", return_value=mock_arrangements):
                with patch(
                    "src.employees.services.get_subordinates_by_manager_id",
                    return_value=[mock_employee],
                ):
                    with patch(
                        "src.arrangements.services.create_presigned_url",
                        side_effect=mock_presigned_url,
                    ):
                        result = get_team_arrangements(
                            mock_db_session, staff_id=1, current_approval_status=[]
                        )

        assert isinstance(result, dict)
        assert "peers" in result
        assert "subordinates" in result
        assert len(result["peers"]) == 1
        assert len(result["subordinates"][0]) == 1  # second item is the pagination meta data
        assert (
            result["peers"][0].supporting_doc_1
            == "https://example.com/presigned-url/test_file_1.pdf"
        )
        assert (
            result["peers"][0].supporting_doc_2
            == "https://example.com/presigned-url/test_file_2.pdf"
        )
        assert (
            result["subordinates"][0].supporting_doc_1
            == "https://example.com/presigned-url/test_file_1.pdf"
        )
        assert (
            result["subordinates"][0].supporting_doc_2
            == "https://example.com/presigned-url/test_file_2.pdf"
        )

    def test_no_peers_or_subordinates(self, mock_db_session):
        with patch("src.employees.services.get_peers_by_staff_id", return_value=[]):
            with patch("src.employees.services.get_subordinates_by_manager_id", return_value=[]):
                with patch("src.arrangements.crud.get_arrangements", return_value=[]):
                    result = get_team_arrangements(
                        mock_db_session, staff_id=1, current_approval_status=[]
                    )
                    assert isinstance(result, dict)
                    assert result.get("peers", []) == []
                    assert result.get("subordinates", []) == []


class TestCreateArrangementsFromRequest:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "is_jack_sim, is_recurring, num_files",
        [
            (False, False, 0),  # Non-Jack Sim, Non-Recurring, No File
            (False, True, 0),  # Non-Jack Sim, Recurring, No File
            (False, False, 1),  # Non-Jack Sim, Non-Recurring, Single File
            (False, True, 1),  # Non-Jack Sim, Recurring, Single File
            (False, False, 2),  # Non-Jack Sim, Non-Recurring, Multiple Files
            (False, True, 2),  # Non-Jack Sim, Recurring, Multiple Files
            (True, False, 0),  # Jack Sim, Non-Recurring, No File
        ],
    )
    @patch("src.utils.convert_model_to_pydantic_schema")
    @patch("src.utils.fit_schema_to_model")
    @patch("src.arrangements.crud.create_arrangements")
    @patch("src.arrangements.services.expand_recurring_arrangement")
    @patch("src.arrangements.crud.create_recurring_request")
    @patch("src.arrangements.services.upload_file")
    @patch("src.employees.services.get_manager_by_subordinate_id")
    async def test_success(
        self,
        mock_get_manager,
        mock_upload_file,
        mock_create_recurring,
        mock_expand_recurring,
        mock_create_arrangements,
        mock_fit,
        mock_convert,
        is_jack_sim,
        is_recurring,
        num_files,
        mock_s3_client,
        mock_db_session,
        mock_manager,
        mock_arrangement_data,
    ):
        # AAA Reference: https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
        # Arrange
        repeat_num = 1
        if is_recurring:
            repeat_num = 2

        mock_wfh_request = MagicMock(spec=ArrangementCreateWithFile)
        mock_wfh_request.configure_mock(
            staff_id=1 if not is_jack_sim else 130002,
            is_recurring=is_recurring,
            update_datetime=datetime.now(),
            current_approval_status="pending approval",
        )
        mock_supporting_docs = [MagicMock(spec=File)] * num_files

        mock_get_manager.return_value = mock_manager if not is_jack_sim else None
        mock_upload_file.return_value = {"file_url": "https://s3-bucket/test_file.pdf"}

        if is_recurring:
            mock_create_recurring.return_value = MagicMock(spec=arrangement_models.RecurringRequest)
            mock_create_recurring.configure_mock(batch_id=1)
            mock_expand_recurring.return_value = [
                MagicMock(spec=ArrangementCreateWithFile) for _ in range(repeat_num)
            ]

        mock_fit.return_value = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_create_arrangements.return_value = [
            MagicMock(spec=arrangement_models.LatestArrangement) for _ in range(repeat_num)
        ]
        mock_convert.return_value = ArrangementCreateResponse(**mock_arrangement_data)

        # Act
        result = await create_arrangements_from_request(
            mock_db_session,
            mock_wfh_request,
            mock_supporting_docs,
        )

        # Assert
        if is_jack_sim:
            assert mock_wfh_request.current_approval_status == "approved"
            assert mock_wfh_request.approving_officer is None
        else:
            assert mock_wfh_request.current_approval_status == "pending approval"
            assert mock_wfh_request.approving_officer == mock_manager.staff_id

        mock_get_manager.assert_called_once_with(mock_db_session, mock_wfh_request.staff_id)

        if num_files > 0:
            mock_upload_file.assert_called_with(
                mock_wfh_request.staff_id,
                str(mock_wfh_request.update_datetime),
                mock_supporting_docs[0],
                mock_s3_client,
            )
            assert mock_upload_file.call_count == num_files
        else:
            mock_upload_file.assert_not_called()

        if not is_recurring:
            mock_create_recurring.assert_not_called()
            mock_expand_recurring.assert_not_called()
            mock_fit.assert_called_once_with(mock_wfh_request, arrangement_models.LatestArrangement)
        else:
            mock_create_recurring.assert_called_once_with(mock_db_session, mock_wfh_request)
            mock_expand_recurring.assert_called_once_with(
                mock_wfh_request, mock_create_recurring.return_value.batch_id
            )
            for call_args in mock_expand_recurring.return_value:
                mock_fit.assert_any_call(call_args, arrangement_models.LatestArrangement)
            assert mock_fit.call_count == repeat_num

        mock_create_arrangements.assert_called_once_with(
            mock_db_session, [mock_fit.return_value for _ in range(repeat_num)]
        )
        mock_convert.assert_called_once_with(
            mock_create_arrangements.return_value, ArrangementCreateResponse
        )
        assert result == mock_convert.return_value

    @pytest.mark.asyncio
    @patch("src.arrangements.services.upload_file")
    @patch("src.employees.services.get_manager_by_subordinate_id")
    async def test_file_upload_failure(self, mock_get_manager, mock_upload_file, mock_db_session):
        # Arrange
        error_response = {
            "Error": {"Code": "NoSuchBucket", "Message": "The specified bucket does not exist"}
        }
        operation_name = "PutObject"
        mock_upload_file.side_effect = botocore.exceptions.ClientError(
            error_response, operation_name
        )
        mock_wfh_request = MagicMock(spec=ArrangementCreateWithFile)
        mock_wfh_request.configure_mock(
            staff_id=1,
            update_datetime=datetime.now(),
        )
        mock_supporting_documents = [MagicMock(spec=File)]

        # Act and Assert
        with pytest.raises(arrangement_exceptions.S3UploadFailedException):
            await create_arrangements_from_request(
                mock_db_session,
                mock_wfh_request,
                mock_supporting_documents,
            )

    @pytest.mark.asyncio
    @patch("src.arrangements.crud.create_recurring_request", side_effect=SQLAlchemyError)
    @patch("src.employees.services.get_manager_by_subordinate_id")
    async def test_sqlalchemy_error(self, mock_get_manager, mock_create_recurring, mock_db_session):
        mock_wfh_request = MagicMock(spec=ArrangementCreateWithFile)
        mock_wfh_request.configure_mock(
            staff_id=1,
            is_recurring=True,
            update_datetime=datetime.now(),
        )
        with pytest.raises(SQLAlchemyError):
            await create_arrangements_from_request(
                mock_db_session,
                mock_wfh_request,
                [],
            )


class TestExpandRecurringArrangement:
    def format_date_string(self, date_string):
        return datetime.strptime(date_string, "%Y-%m-%d").date()

    @pytest.mark.parametrize(
        (
            "start_date",
            "recurring_frequency_unit",
            "recurring_frequency_number",
            "recurring_occurrences",
        ),
        [
            ("2024-01-01", "week", 1, 3),
            ("2024-01-01", "month", 1, 3),
            ("2024-01-31", "week", 1, 3),
            ("2024-01-31", "month", 1, 3),
        ],
    )
    def test_success(
        self,
        start_date,
        recurring_frequency_unit,
        recurring_frequency_number,
        recurring_occurrences,
    ):
        wfh_request = create_mock_arrangement_create_with_file(
            is_recurring=True,
            recurring_frequency_unit=recurring_frequency_unit,
            recurring_frequency_number=recurring_frequency_number,
            recurring_occurrences=recurring_occurrences,
            wfh_date=start_date,
        )
        batch_id = 1
        result = expand_recurring_arrangement(wfh_request, batch_id)

        if (
            start_date == "2024-01-01"
            and recurring_frequency_unit == "week"
            and recurring_frequency_number == 1
            and recurring_occurrences == 3
        ):
            expected_dates = ["2024-01-01", "2024-01-08", "2024-01-15"]
        elif (
            start_date == "2024-01-01"
            and recurring_frequency_unit == "month"
            and recurring_frequency_number == 1
            and recurring_occurrences == 3
        ):
            expected_dates = ["2024-01-01", "2024-02-01", "2024-03-01"]
        elif (
            start_date == "2024-01-31"
            and recurring_frequency_unit == "week"
            and recurring_frequency_number == 1
            and recurring_occurrences == 3
        ):
            expected_dates = ["2024-01-31", "2024-02-07", "2024-02-14"]
        else:  # Test for leap year
            expected_dates = ["2024-01-31", "2024-02-29", "2024-03-31"]

        for i in range(recurring_occurrences):
            assert result[i].wfh_date == self.format_date_string(expected_dates[i])

        assert len(result) == recurring_occurrences
        assert all(arr.batch_id == batch_id for arr in result)


class TestUpdateArrangementApprovalStatus:
    def test_success(self, mock_db_session):
        mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_arrangement.arrangement_id = 1

        wfh_update = ArrangementUpdate(
            arrangement_id=1,
            STATUS="approve",
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
    async def test_not_found(self, mock_db_session):
        wfh_update = ArrangementUpdate(
            arrangement_id=1,
            STATUS="approve",
            approving_officer=2,
            reason_description="Approved by manager",
        )

        with patch("src.arrangements.crud.get_arrangement_by_id", return_value=None):
            with pytest.raises(arrangement_exceptions.ArrangementNotFoundException):
                await update_arrangement_approval_status(mock_db_session, wfh_update)

    @pytest.mark.parametrize(
        "STATUS, expected_status",
        [
            ("approve", "approved"),
            ("reject", "rejected"),
            ("withdraw", "withdrawn"),
            ("cancel", "cancelled"),
        ],
    )
    def test_STATUSs(self, mock_db_session, STATUS, expected_status):
        mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_arrangement.arrangement_id = 1

        wfh_update = ArrangementUpdate(
            arrangement_id=1,
            STATUS=STATUS,
            approving_officer=2,
            reason_description="STATUS taken",
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
                assert result.reason_description == "STATUS taken"

    def test_invalid_STATUS(self, mock_db_session):
        mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_arrangement.arrangement_id = 1

        wfh_update = ArrangementUpdate(
            arrangement_id=1,
            STATUS="approve",  # Use a valid STATUS
            approving_officer=2,
            reason_description="Invalid STATUS test",
        )

        with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
            with patch.dict(STATUS, {"approve": None}):  # Make 'approve' STATUS invalid
                with pytest.raises(ValueError, match="Invalid STATUS: approve"):
                    update_arrangement_approval_status(mock_db_session, wfh_update)

    def test_update_arrangement_approval_status_default_reason(self, mock_db_session):
        mock_arrangement = MagicMock(spec=arrangement_models.LatestArrangement)
        mock_arrangement.arrangement_id = 1

        wfh_update = ArrangementUpdate(
            arrangement_id=1,
            STATUS="approve",
            approving_officer=2,
            reason_description=None,
        )

        with patch("src.arrangements.crud.get_arrangement_by_id", return_value=mock_arrangement):
            with patch(
                "src.arrangements.crud.update_arrangement_approval_status",
                return_value=mock_arrangement,
            ):
                result = update_arrangement_approval_status(mock_db_session, wfh_update)

                assert result.reason_description == "[DEFAULT] Approved by Manager"


# @pytest.mark.asyncio
# async def test_create_arrangements_from_request_file_upload_failure(mock_db_session, mock_employee):
#     wfh_request = create_mock_arrangement_create_with_file()

#     mock_file = MagicMock()

#     with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
#         with patch("src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}):
#             with patch("src.arrangements.services.boto3.client"):
#                 with patch(
#                     "src.arrangements.utils.upload_file", side_effect=Exception("Upload failed")
#                 ):
#                     with pytest.raises(HTTPException) as exc_info:
#                         await create_arrangements_from_request(
#                             mock_db_session, wfh_request, [mock_file]
#                         )
#                     assert exc_info.value.status_code == 500
#                     assert "Error uploading files" in str(exc_info.value.detail)

# TODO: Fix this test
# def test_update_arrangement_approval_status_invalid_STATUS_exception(mock_db_session):
#     with pytest.raises(
#         ValueError, match="Input should be 'approve', 'reject', 'withdraw' or 'cancel'"
#     ):
#         wfh_update = ArrangementUpdate(
#             arrangement_id=1,
#             STATUS="invalid_STATUS",
#             approving_officer=2,
#             reason_description="Invalid STATUS test",
#         )


def test_returns_delegate_approving_officer_info():
    # Arrange: Mock an arrangement with a delegate approving officer
    arrangement = MagicMock()
    arrangement.delegate_approving_officer = True
    arrangement.delegate_approving_officer_info = "Delegate Officer Info"
    arrangement.approving_officer_info = "Original Officer Info"

    # Act: Call the function with the mocked arrangement
    result = get_approving_officer(arrangement)

    # Assert: Check if the delegate approving officer info is returned
    assert result == "Delegate Officer Info"


def test_returns_original_approving_officer_info():
    # Arrange: Mock an arrangement without a delegate approving officer
    arrangement = MagicMock()
    arrangement.delegate_approving_officer = False  # No delegate
    arrangement.delegate_approving_officer_info = None
    arrangement.approving_officer_info = "Original Officer Info"

    # Act: Call the function with the mocked arrangement
    result = get_approving_officer(arrangement)

    # Assert: Check if the original approving officer info is returned
    assert result == "Original Officer Info"


# ======================== DEPRECATED TESTS ========================
# class TestCreateArrangementsFromRequest:
# @pytest.mark.asyncio
# async def test_recurring(self, mock_db_session, mock_employee):
#     wfh_request = create_mock_arrangement_create_with_file(
#         is_recurring=True,
#         recurring_frequency_unit="week",
#         recurring_frequency_number=1,
#         recurring_occurrences=3,
#     )

#     mock_batch = MagicMock(spec=arrangement_models.RecurringRequest)
#     mock_batch.batch_id = 1

#     with patch("src.arrangements.crud.create_recurring_request", return_value=mock_batch):
#         with patch(
#             "src.arrangements.services.expand_recurring_arrangement",
#             return_value=[wfh_request, wfh_request, wfh_request],
#         ):
#             with patch(
#                 "src.arrangements.crud.create_arrangements",
#                 return_value=[MagicMock(spec=arrangement_models.LatestArrangement)],
#             ):
#                 with patch(
#                     "src.utils.convert_model_to_pydantic_schema",
#                     return_value=["arrangement_schema"],
#                 ):
#                     with patch(
#                         "src.employees.crud.get_employee_by_staff_id",
#                         return_value=mock_employee,
#                     ):
#                         with patch(
#                             "src.arrangements.services.fetch_manager_info",
#                             return_value={"manager_id": 2},
#                         ):
#                             with patch("src.arrangements.services.boto3.client"):
#                                 with patch(
#                                     "src.arrangements.utils.upload_file",
#                                     return_value={"file_url": "https://example.com/file.pdf"},
#                                 ):
#                                     result = await create_arrangements_from_request(
#                                         mock_db_session, wfh_request, []
#                                     )
#                                     assert len(result) == 1
#                                     assert result[0] == "arrangement_schema"
#
# @pytest.mark.asyncio
# @patch("src.arrangements.crud.create_arrangements", side_effect=Exception("Failed"))
# async def test_failure(self, mock_db_session):
#     with pytest.raises(Exception):
#         await create_arrangements_from_request(mock_db_session, MagicMock(), [])

# TODO: Move to routes or schema validation
# @pytest.mark.asyncio
# async def test_file_upload_unsupported_format(self, mock_db_session, mock_employee):
#     wfh_request = create_mock_arrangement_create_with_file()
#     mock_file = MagicMock()

#     with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
#         with patch(
#             "src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}
#         ):
#             with patch("src.arrangements.services.boto3.client"):
#                 with patch(
#                     "src.arrangements.utils.upload_file",
#                     side_effect=Exception(
#                         "Error uploading files: 400: Invalid file type. Supported file types are JPEG, PNG, and PDF"
#                     ),
#                 ):
#                     with pytest.raises(HTTPException) as exc_info:
#                         await create_arrangements_from_request(
#                             mock_db_session, wfh_request, [mock_file]
#                         )
#                     assert exc_info.value.status_code == 500
#                     assert (
#                         "Invalid file type. Supported file types are JPEG, PNG, and PDF"
#                         in str(exc_info.value.detail)
#                     )
#
# @pytest.mark.asyncio
# async def test_missing_required_fields(self, mock_db_session, mock_employee):
#     with pytest.raises(ValueError, match="Input should be 'full', 'am' or 'pm'"):
#         create_mock_arrangement_create_with_file(wfh_type=None)

# @pytest.mark.asyncio
# async def test_file_deletion_on_error(self, mock_db_session, mock_employee):
#     wfh_request = create_mock_arrangement_create_with_file()
#     mock_file = MagicMock()

#     with patch("src.employees.crud.get_employee_by_staff_id", return_value=mock_employee):
#         with patch(
#             "src.arrangements.services.fetch_manager_info", return_value={"manager_id": 2}
#         ):
#             with patch("src.arrangements.services.boto3.client"):
#                 with patch(
#                     "src.arrangements.utils.upload_file", return_value={"file_url": "test_url"}
#                 ):
#                     with patch(
#                         "src.arrangements.crud.create_arrangements",
#                         side_effect=Exception("DB Error"),
#                     ):
#                         with patch("src.arrangements.utils.delete_file"):
#                             with pytest.raises(HTTPException) as exc_info:
#                                 await create_arrangements_from_request(
#                                     mock_db_session, wfh_request, [mock_file]
#                                 )
#                             assert exc_info.value.status_code == 500
#                             assert (
#                                 "Invalid file type. Supported file types are JPEG, PNG, and PDF"
#                                 in str(exc_info.value.detail)
#                             )

# REVIEW: These should be tested by the schema validation
# class TestExpandRecurringArrangement:
#     def test_zero_occurrences(self):
#         with pytest.raises(
#             ValueError,
#             match="When 'is_recurring' is True, 'recurring_occurrences' must have a non-zero value",
#         ):
#             create_mock_arrangement_create_with_file(
#                 is_recurring=True,
#                 recurring_frequency_unit="week",
#                 recurring_frequency_number=1,
#                 recurring_occurrences=0,
#             )

#     def test_invalid_frequency_unit(self):
#         with pytest.raises(ValueError, match="Input should be 'week' or 'month'"):
#             create_mock_arrangement_create_with_file(
#                 is_recurring=True,
#                 recurring_frequency_unit="invalid_unit",
#                 recurring_frequency_number=1,
#                 recurring_occurrences=3,
#             )
