from datetime import datetime
from typing import List
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import botocore
import botocore.exceptions
import httpx
import pytest
from fastapi import File
from fastapi.testclient import TestClient
from src.app import app
from src.arrangements.commons import dataclasses as dc
from src.arrangements.commons import exceptions as arrangement_exceptions
from src.arrangements.commons.enums import Action, ApprovalStatus
from src.arrangements.services import (
    auto_reject_old_requests,
    create_arrangements_from_request,
    get_all_arrangements,
    get_arrangement_by_id,
    get_arrangement_logs,
    get_personal_arrangements,
    get_subordinates_arrangements,
    get_team_arrangements,
    update_arrangement_approval_status,
)
from src.employees import exceptions as employee_exceptions
from src.employees.models import DelegateLog
from src.employees.schemas import EmployeeBase
from src.tests.test_utils import mock_db_session  # noqa: F401, E261

client = TestClient(app)
singapore_timezone = ZoneInfo("Asia/Singapore")


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
        "update_datetime": datetime.now(singapore_timezone),
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


# def create_mock_arrangement_create_with_file(**kwargs):
#     default_data = {
#         "staff_id": 1,
#         "wfh_date": "2024-01-01",
#         "wfh_type": "full",
#         "reason_description": "Work from home request",
#         "is_recurring": False,
#         "approving_officer": None,
#         "update_datetime": datetime.now(singapore_timezone),
#         "current_approval_status": "pending approval",
#         "supporting_doc_1": None,
#         "supporting_doc_2": None,
#         "supporting_doc_3": None,
#     }
#     default_data.update(kwargs)
#     return ArrangementCreateWithFile(**default_data)


# Mock the httpx.AsyncClient.get method
async def mock_get(*args, **kwargs):
    return httpx.Response(200, json={"manager_id": 2})


# Mock the upload_file function
# async def mock_upload_file(*args, **kwargs):
#     return {"file_url": "https://s3-bucket/test_file.pdf"}


@patch("src.arrangements.crud.get_arrangement_by_id")
class TestGetArrangementById:
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    def test_success(self, mock_get_arrangement, mock_convert, mock_db_session):
        get_arrangement_by_id(mock_db_session, arrangement_id=1)

        mock_get_arrangement.assert_called_once()
        mock_convert.assert_called_once()

    def test_not_found_failure(self, mock_get_arrangement, mock_db_session):
        mock_get_arrangement.return_value = None
        with pytest.raises(arrangement_exceptions.ArrangementNotFoundException):
            get_arrangement_by_id(mock_db_session, arrangement_id=1)


class TestGetAllArrangements:
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangements")
    def test_success(self, mock_get_arrangements, mock_convert, mock_db_session):
        # Arrange
        mock_get_arrangements.return_value = [MagicMock(spec=dc.ArrangementResponse)]

        # Act
        get_all_arrangements(mock_db_session, filters=dc.ArrangementFilters())

        # Assert
        mock_get_arrangements.assert_called_once()
        mock_convert.assert_called()


class TestGetPersonalArrangements:
    @pytest.mark.parametrize(
        ("current_approval_status", "num_arrangements"),
        [
            ([ApprovalStatus.PENDING_APPROVAL], 1),
            ([ApprovalStatus.PENDING_APPROVAL], 3),
            ([ApprovalStatus.PENDING_APPROVAL], 0),
            ([ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.APPROVED], 1),
            ([], 1),
        ],
    )
    @patch("src.arrangements.services.create_presigned_url")
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangements")
    def test_success(
        self,
        mock_get_arrangements,
        mock_convert,
        mock_create_presigned_url,
        current_approval_status,
        num_arrangements,
        mock_db_session,
    ):
        # Arrange
        mock_get_arrangements.return_value = [
            MagicMock(spec=dc.ArrangementResponse)
        ] * num_arrangements

        group_by_date = (
            False  # always False since it is deprecated, but retained for backwards compatibility
        )
        filters = dc.ArrangementFilters(group_by_date=group_by_date)

        # Act
        get_personal_arrangements(mock_db_session, staff_id=1, filters=filters)

        # Assert
        mock_get_arrangements.assert_called_once()

        if num_arrangements == 0:
            mock_convert.assert_not_called()
        else:
            mock_convert.assert_called()
            assert mock_convert.call_count == num_arrangements


class TestGetSubordinatesArrangements:
    @patch("src.arrangements.services.group_arrangements_by_date")
    @patch("src.arrangements.services.create_presigned_url")
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangements")
    @pytest.mark.parametrize(
        ("supporting_docs", "group_by_date"),
        [
            ([None, None, None], False),
            (["/140002/2024-10-12T14:30:00/test_file_1.pdf", None, None], False),
            (["/140002/2024-10-12T14:30:00/test_file_1.pdf", None, None], False),
            (
                [
                    "/140002/2024-10-12T14:30:00/test_file_1.pdf",
                    "/140002/2024-10-12T14:30:00/test_file_2.pdf",
                    "/1/2024-10-12T14:30:00/test_file_3.pdf",
                ],
                False,
            ),
        ],
    )
    def test_success(
        self,
        mock_get_arrangements,
        mock_convert,
        mock_create_presigned_url,
        mock_group_arrangements,
        supporting_docs,
        group_by_date,
        mock_db_session,
        mock_presigned_url,
    ):
        # Arrange
        mock_get_arrangements.return_value = [MagicMock(spec=dc.ArrangementResponse)]

        mock_arrangement = MagicMock(spec=dc.ArrangementResponse)
        mock_arrangement.configure_mock(
            supporting_doc_1=supporting_docs[0],
            supporting_doc_2=supporting_docs[1],
            supporting_doc_3=supporting_docs[2],
        )

        mock_convert.return_value = mock_arrangement
        mock_create_presigned_url.side_effect = [mock_presigned_url(doc) for doc in supporting_docs]
        mock_group_arrangements.return_value = [MagicMock(spec=dc.CreatedArrangementGroupByDate)]

        manager_id = 1
        items_per_page = 10
        page_num = 1

        # Act
        result = get_subordinates_arrangements(
            db=mock_db_session,
            manager_id=manager_id,
            filters=dc.ArrangementFilters(group_by_date=group_by_date),
            pagination=dc.PaginationConfig(items_per_page=items_per_page, page_num=page_num),
        )

        # Assert
        mock_get_arrangements.assert_called_once()
        mock_convert.assert_called()
        mock_create_presigned_url.assert_called()
        assert mock_create_presigned_url.call_count == 3
        if group_by_date:
            mock_group_arrangements.assert_called_once()
        else:
            mock_group_arrangements.assert_not_called()

        assert isinstance(result, tuple)
        assert len(result) == 2  # return data and pagination metadata

        arrangements, pagination_meta = result

        assert isinstance(arrangements, List)

        if group_by_date:
            assert isinstance(arrangements[0], dc.CreatedArrangementGroupByDate)
        else:
            assert isinstance(arrangements[0], dc.ArrangementResponse)

        assert isinstance(pagination_meta, dc.PaginationMeta)


class TestGetTeamArrangements:
    @pytest.mark.parametrize(
        "group_by_date",
        [True, False],
    )
    @patch("src.arrangements.services.compute_pagination_meta")
    @patch("src.arrangements.services.group_arrangements_by_date")
    @patch("src.arrangements.services.create_presigned_url")
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangements")
    @patch("src.employees.services.get_peers_by_staff_id")
    def test_success(
        self,
        mock_get_peers,
        mock_get_arrangements,
        mock_convert,
        mock_create_presigned_url,
        mock_group_arrangements,
        mock_compute_pagination_meta,
        group_by_date,
        mock_db_session,
        mock_arrangement_data,
        mock_employee,
    ):
        # Arrange
        mock_get_peers.return_value = [mock_employee]
        mock_get_arrangements.return_value = [mock_arrangement_data]
        mock_convert.return_value = MagicMock(spec=dc.ArrangementResponse)
        mock_group_arrangements.return_value = [MagicMock(spec=dc.CreatedArrangementGroupByDate)]
        mock_compute_pagination_meta.return_value = MagicMock(spec=dc.PaginationMeta)

        # Act
        result = get_team_arrangements(
            db=mock_db_session,
            staff_id=1,
            filters=dc.ArrangementFilters(group_by_date=group_by_date),
            pagination=dc.PaginationConfig(),
        )

        # Assert
        mock_get_peers.assert_called_once()
        mock_get_arrangements.assert_called()
        assert mock_get_arrangements.call_count == 2
        mock_convert.assert_called()

        if group_by_date:
            mock_group_arrangements.assert_called_once()
        else:
            mock_group_arrangements.assert_not_called()

        assert isinstance(result, tuple)
        assert len(result) == 2  # return data and pagination metadata

        arrangements, pagination_meta = result

        assert isinstance(arrangements, List)

        if group_by_date:
            assert isinstance(arrangements[0], dc.CreatedArrangementGroupByDate)
        else:
            assert isinstance(arrangements[0], dc.ArrangementResponse)

        assert isinstance(pagination_meta, dc.PaginationMeta)


class TestGetArrangementLogs:
    @patch("src.arrangements.commons.dataclasses.ArrangementLogResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangement_logs")
    def test_success(self, mock_get_logs, mock_convert, mock_db_session):
        mock_get_logs.return_value = [MagicMock(spec=dc.ArrangementLogResponse)]
        mock_convert.return_value = MagicMock(spec=dc.ArrangementLogResponse)

        get_arrangement_logs(mock_db_session)

        mock_get_logs.assert_called_once()
        mock_convert.assert_called()


class TestCreateArrangementsFromRequest:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("is_jack_sim, has_delegation, is_recurring, num_files"),
        [
            (False, False, False, 0),  # Non-Jack Sim, Non-Recurring, No File
            (False, True, False, 0),  # Non-Jack Sim, Non-Recurring, No File
            (False, False, True, 0),  # Non-Jack Sim, Recurring, No File
            (False, False, False, 1),  # Non-Jack Sim, Non-Recurring, Single File
            (False, False, True, 1),  # Non-Jack Sim, Recurring, Single File
            (False, False, False, 2),  # Non-Jack Sim, Non-Recurring, Multiple Files
            (False, False, True, 2),  # Non-Jack Sim, Recurring, Multiple Files
            (True, False, False, 0),  # Jack Sim, Non-Recurring, No File
        ],
    )
    @patch("src.arrangements.services.craft_and_send_email")
    @patch("src.arrangements.crud.create_arrangements")
    @patch("src.arrangements.services.expand_recurring_arrangement")
    @patch("src.arrangements.crud.create_recurring_request")
    @patch("src.arrangements.commons.dataclasses.RecurringRequestDetails.from_dict")
    @patch("src.arrangements.services.upload_file")
    @patch("src.employees.crud.get_existing_delegation")
    @patch("src.employees.services.get_manager_by_subordinate_id")
    @patch("src.employees.crud.get_employee_by_staff_id")
    @patch("src.arrangements.services.asdict")
    async def test_success(
        self,
        mock_asdict,
        mock_get_employee,
        mock_get_manager,
        mock_get_delegation,
        mock_upload_file,
        mock_convert_recurring,
        mock_create_recurring,
        mock_expand_recurring,
        mock_create_arrangements,
        mock_craft_send_email,
        is_jack_sim,
        has_delegation,
        is_recurring,
        num_files,
        mock_db_session,
        mock_manager,
        mock_employee,
    ):
        # AAA Reference: https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/
        # Arrange
        repeat_num = 1
        if is_recurring:
            repeat_num = 2

        mock_wfh_request = MagicMock(spec=dc.CreateArrangementRequest)
        mock_wfh_request.configure_mock(
            requester_staff_id=1 if not is_jack_sim else 130002,
            is_recurring=is_recurring,
            update_datetime=datetime.now(singapore_timezone),
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            wfh_date=datetime.now(singapore_timezone).date(),
            batch_id=None,
            approving_officer=None,
        )
        mock_supporting_docs = [MagicMock(spec=File)] * num_files

        mock_get_employee.return_value = mock_employee

        mock_get_manager.return_value = mock_manager, None
        if is_jack_sim:
            mock_get_manager.return_value = None, None

        mock_get_delegation.return_value = None
        if has_delegation:
            mock_delegation = MagicMock(spec=DelegateLog)
            mock_delegation.configure_mock(delegate_manager_id=1)
            mock_get_delegation.return_value = mock_delegation

        mock_upload_file.return_value = {"file_url": "https://s3-bucket/test_file.pdf"}

        if is_recurring:
            mock_create_recurring.return_value = MagicMock(spec=dc.CreatedRecurringRequest)
            mock_create_recurring.return_value.configure_mock(batch_id=1)
            mock_expand_recurring.return_value = [
                MagicMock(spec=dc.CreateArrangementRequest) for _ in range(repeat_num)
            ]

        mock_create_arrangements.return_value = [
            MagicMock(spec=dc.ArrangementResponse) for _ in range(repeat_num)
        ]

        # Act
        await create_arrangements_from_request(
            mock_db_session,
            mock_wfh_request,
            mock_supporting_docs,
        )

        # Assert
        if is_jack_sim:
            assert mock_wfh_request.current_approval_status == ApprovalStatus.APPROVED
            assert mock_wfh_request.approving_officer is None
            mock_get_delegation.assert_not_called()
        else:
            assert mock_wfh_request.current_approval_status == ApprovalStatus.PENDING_APPROVAL
            assert mock_wfh_request.approving_officer == mock_manager.staff_id
            mock_get_delegation.assert_called_once()

        mock_get_employee.assert_called_once()
        mock_get_manager.assert_called_once()

        if num_files > 0:
            mock_upload_file.assert_called()
            assert mock_upload_file.call_count == num_files
        else:
            mock_upload_file.assert_not_called()

        if not is_recurring:
            mock_create_recurring.assert_not_called()
            mock_expand_recurring.assert_not_called()
        else:
            mock_create_recurring.assert_called_once()
            mock_expand_recurring.assert_called_once()

        mock_create_arrangements.assert_called_once()
        mock_craft_send_email.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "successful_uploads",
        [
            [{"file_url": "s3://bucket/test_file_1.pdf"}],
            [{"file_url": "s3://bucket/test_file_1.pdf"}],
            [
                {"file_url": "s3://bucket/test_file_1.pdf"},
                {"file_url": "s3://bucket/test_file_2.pdf"},
            ],
            [],
        ],
    )
    @patch("src.arrangements.services.handle_multi_file_deletion")
    @patch("src.arrangements.services.upload_file")
    @patch("src.employees.services.get_manager_by_subordinate_id")
    @patch("src.employees.crud.get_employee_by_staff_id")
    async def test_file_s3_failure(
        self,
        mock_get_employee,
        mock_get_manager,
        mock_upload_file,
        mock_delete_file,
        successful_uploads,
        mock_db_session,
    ):
        # Arrange
        error_response = {
            "Error": {"Code": "NoSuchBucket", "Message": "The specified bucket does not exist"}
        }
        operation_name = "PutObject"

        mock_wfh_request = MagicMock(spec=dc.CreateArrangementRequest)
        mock_wfh_request.configure_mock(
            requester_staff_id=1,
            update_datetime=datetime.now(singapore_timezone),
        )

        mock_get_employee.return_value = MagicMock(spec=EmployeeBase)
        mock_get_employee.return_value.configure_mock(
            requester_staff_id=1,
        )
        mock_get_manager.return_value = None, None

        upload_side_effects = successful_uploads.copy()
        upload_side_effects.append(botocore.exceptions.ClientError(error_response, operation_name))
        mock_upload_file.side_effect = upload_side_effects

        mock_supporting_documents = [MagicMock(spec=File)] * len(upload_side_effects)

        # Act and Assert
        with pytest.raises(arrangement_exceptions.S3UploadFailedException):
            await create_arrangements_from_request(
                mock_db_session,
                mock_wfh_request,
                mock_supporting_documents,
            )
        mock_delete_file.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.employees.crud.get_employee_by_staff_id", return_value=None)
    async def test_failure_employee_not_found(self, mock_get_employee, mock_db_session):
        mock_request = MagicMock(spec=dc.CreateArrangementRequest)
        mock_request.configure_mock(requester_staff_id=1)

        with pytest.raises(employee_exceptions.EmployeeNotFoundException):
            await create_arrangements_from_request(
                db=mock_db_session,
                wfh_request=mock_request,
                supporting_docs=[],
            )


class TestUpdateArrangementApprovalStatus:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("action", "approval_status"),
        [
            (Action.APPROVE, ApprovalStatus.PENDING_APPROVAL),
            (Action.REJECT, ApprovalStatus.PENDING_APPROVAL),
            (Action.APPROVE, ApprovalStatus.PENDING_WITHDRAWAL),
            (Action.REJECT, ApprovalStatus.PENDING_WITHDRAWAL),
            (Action.WITHDRAW, ApprovalStatus.APPROVED),
            (Action.CANCEL, ApprovalStatus.PENDING_APPROVAL),
        ],
    )
    @patch("src.arrangements.services.craft_and_send_email")
    @patch("src.employees.crud.get_employee_by_staff_id")
    @patch("src.arrangements.crud.update_arrangement_approval_status")
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangement_by_id")
    async def test_success_status(
        self,
        mock_get_arrangement,
        mock_convert,
        mock_update,
        mock_get_employee,
        mock_craft_send_email,
        action,
        approval_status,
        mock_db_session,
    ):
        mock_wfh_update = MagicMock(spec=dc.UpdateArrangementRequest)
        mock_wfh_update.configure_mock(
            arrangement_id=1,
            action=action,
            approving_officer=2,
            status_reason="Approved by manager",
        )

        mock_get_arrangement.return_value = MagicMock()
        mock_convert.return_value = MagicMock(spec=dc.ArrangementResponse)
        mock_convert.return_value.configure_mock(
            requester_staff_id=1,
            current_approval_status=approval_status,
        )
        mock_update.return_value = MagicMock()
        mock_get_employee.return_value = MagicMock()

        await update_arrangement_approval_status(mock_db_session, mock_wfh_update, None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("action", "approval_status"),
        [
            (Action.APPROVE, ApprovalStatus.APPROVED),
            (Action.APPROVE, ApprovalStatus.REJECTED),
            (Action.APPROVE, ApprovalStatus.WITHDRAWN),
            (Action.APPROVE, ApprovalStatus.CANCELLED),
            (Action.REJECT, ApprovalStatus.APPROVED),
            (Action.REJECT, ApprovalStatus.REJECTED),
            (Action.REJECT, ApprovalStatus.WITHDRAWN),
            (Action.REJECT, ApprovalStatus.CANCELLED),
            (Action.WITHDRAW, ApprovalStatus.REJECTED),
            (Action.WITHDRAW, ApprovalStatus.WITHDRAWN),
            (Action.WITHDRAW, ApprovalStatus.CANCELLED),
            (Action.WITHDRAW, ApprovalStatus.PENDING_APPROVAL),
            (Action.WITHDRAW, ApprovalStatus.PENDING_WITHDRAWAL),
            (Action.CANCEL, ApprovalStatus.APPROVED),
            (Action.CANCEL, ApprovalStatus.REJECTED),
            (Action.CANCEL, ApprovalStatus.WITHDRAWN),
            (Action.CANCEL, ApprovalStatus.CANCELLED),
            (Action.CANCEL, ApprovalStatus.PENDING_WITHDRAWAL),
        ],
    )
    @patch("src.arrangements.commons.dataclasses.ArrangementResponse.from_dict")
    @patch("src.arrangements.crud.get_arrangement_by_id")
    async def test_failure_status(
        self,
        mock_get_arrangement,
        mock_convert,
        action,
        approval_status,
        mock_db_session,
    ):
        mock_wfh_update = MagicMock(spec=dc.UpdateArrangementRequest)
        mock_wfh_update.configure_mock(
            arrangement_id=1,
            action=action,
            approving_officer=2,
            status_reason="Approved by manager",
        )

        mock_get_arrangement.return_value = MagicMock()
        mock_convert.return_value = MagicMock(spec=dc.ArrangementResponse)
        mock_convert.return_value.configure_mock(
            requester_staff_id=1,
            current_approval_status=approval_status,
        )

        with pytest.raises(arrangement_exceptions.ArrangementActionNotAllowedException):
            await update_arrangement_approval_status(mock_db_session, mock_wfh_update, None)

    @pytest.mark.asyncio
    @patch("src.arrangements.crud.get_arrangement_by_id", return_value=None)
    async def test_not_found(self, mock_db_session):
        mock_wfh_update = MagicMock(spec=dc.UpdateArrangementRequest)
        mock_wfh_update.configure_mock(
            arrangement_id=1,
            action=Action.APPROVE,
            approving_officer=2,
            status_reason="Approved by manager",
        )

        with pytest.raises(arrangement_exceptions.ArrangementNotFoundException):
            await update_arrangement_approval_status(
                db=mock_db_session, wfh_update=mock_wfh_update, supporting_docs=[]
            )


@pytest.mark.asyncio
@patch("src.arrangements.services.update_arrangement_approval_status")
@patch("src.arrangements.crud.get_expiring_requests")
@patch("src.arrangements.services.get_db")
class TestAutoRejectOldRequests:
    async def test_success_approving_officer(
        self, mock_get_db, mock_get_expiring_requests, mock_update
    ):
        # Arrange
        mock_get_expiring_requests.return_value = [{"arrangement_id": 1, "approving_officer": 2}]

        # Act
        await auto_reject_old_requests()

        # Assert
        mock_get_db.assert_called_once()
        mock_get_expiring_requests.assert_called_once()
        mock_update.assert_called()
        assert mock_update.call_count == 1

    async def test_success_delegate_approving_officer(
        self, mock_get_db, mock_get_expiring_requests, mock_update
    ):
        # Arrange
        mock_get_expiring_requests.return_value = [
            {"arrangement_id": 1, "delegate_approving_officer": 2}
        ]

        # Act
        await auto_reject_old_requests()

        # Assert
        mock_get_db.assert_called_once()
        mock_get_expiring_requests.assert_called_once()
        mock_update.assert_called()
        assert mock_update.call_count == 1

    async def test_success_no_requests(self, mock_get_db, mock_get_expiring_requests, mock_update):
        # Arrange
        mock_get_expiring_requests.return_value = []

        # Act
        await auto_reject_old_requests()

        # Assert
        mock_get_expiring_requests.assert_called_once()
        mock_update.assert_not_called()

    async def test_failure_unknown(self, mock_get_db, mock_get_expiring_requests, mock_update):
        # Arrange
        mock_get_expiring_requests.return_value = [
            {"arrangement_id": 1, "approving_officer": 1},
            {"arrangement_id": 2, "approving_officer": 1},
        ]
        mock_update.side_effect = [Exception, None]

        # Act
        await auto_reject_old_requests()

        # Assert
        mock_update.assert_called()
        assert mock_update.call_count == 2
