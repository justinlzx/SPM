from datetime import datetime, date, timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from src.arrangements.commons import dataclasses as dc
from src.arrangements.commons.enums import ApprovalStatus, RecurringFrequencyUnit, WfhType
from src.arrangements.utils import (
    compute_pagination_meta,
    create_presigned_url,
    delete_file,
    expand_recurring_arrangement,
    format_arrangement_response,
    format_arrangements_response,
    get_tomorrow_date,
    group_arrangements_by_date,
    upload_file,
)
from src.arrangements.commons.dataclasses import (
    ArrangementResponse,
    CreatedArrangementGroupByDate,
    PaginationMeta,
)
from src.arrangements.commons import schemas
import freezegun

Base = declarative_base()


class MockModel(Base):
    __tablename__ = "mock"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class MockSchema(BaseModel):
    id: int
    name: str


class TestExpandRecurringArrangement:
    def format_date_string(self, date_string):
        return datetime.strptime(date_string, "%Y-%m-%d").date()

    @pytest.mark.parametrize(
        (
            "test_case_id",
            "start_date",
            "recurring_frequency_unit",
            "recurring_frequency_number",
            "recurring_occurrences",
        ),
        [
            (1, "2024-01-01", RecurringFrequencyUnit.WEEKLY, 1, 3),
            (2, "2024-01-01", RecurringFrequencyUnit.MONTHLY, 1, 3),
            (3, "2024-01-31", RecurringFrequencyUnit.WEEKLY, 1, 3),
            (4, "2024-01-31", RecurringFrequencyUnit.MONTHLY, 1, 3),
        ],
    )
    def test_success(
        self,
        test_case_id,
        start_date,
        recurring_frequency_unit,
        recurring_frequency_number,
        recurring_occurrences,
    ):
        wfh_request = MagicMock(spec=dc.CreateArrangementRequest)
        wfh_request.configure_mock(
            wfh_date=self.format_date_string(start_date),
            is_recurring=True,
            recurring_frequency_unit=recurring_frequency_unit,
            recurring_frequency_number=recurring_frequency_number,
            recurring_occurrences=recurring_occurrences,
        )

        result = expand_recurring_arrangement(wfh_request)

        if test_case_id == 1:
            expected_dates = ["2024-01-01", "2024-01-08", "2024-01-15"]
        elif test_case_id == 2:
            expected_dates = ["2024-01-01", "2024-02-01", "2024-03-01"]
        elif test_case_id == 3:
            expected_dates = ["2024-01-31", "2024-02-07", "2024-02-14"]
        else:  # Test for leap year
            expected_dates = ["2024-01-31", "2024-02-29", "2024-03-31"]

        for i in range(recurring_occurrences):
            assert result[i].wfh_date == self.format_date_string(expected_dates[i])

        assert len(result) == recurring_occurrences


class TestGroupArrangementsByDate:
    @pytest.mark.parametrize(
        ("dates", "expected_groups"),
        [
            (
                ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"],
                [("2024-01-02", 2), ("2024-01-01", 2)],
            ),
            (
                ["2024-01-01", "2024-01-02", "2024-01-03"],
                [("2024-01-03", 1), ("2024-01-02", 1), ("2024-01-01", 1)],
            ),
        ],
    )
    def test_success(self, dates, expected_groups):
        mock_arrangements = [MagicMock(spec=dc.ArrangementResponse) for _ in range(len(dates))]
        for i, date in enumerate(dates):
            mock_arrangements[i].wfh_date = datetime.strptime(date, "%Y-%m-%d").date()

        result = group_arrangements_by_date(mock_arrangements)

        assert len(result) == len(expected_groups)
        for i, (date, count) in enumerate(expected_groups):
            assert result[i].date == date
            assert len(result[i].arrangements) == count


@pytest.mark.asyncio
@patch("src.arrangements.utils.boto3.client")
async def test_upload_file_success(mock_s3_client):
    file = MagicMock(spec=UploadFile)
    file.content_type = "image/jpeg"
    file.size = 500 * 1000  # 500 KB
    file.filename = "test.jpg"
    file.file = BytesIO(b"test file content")  # Mock the file-like object

    response = await upload_file(staff_id=1, update_datetime="2024-01-01", file_obj=file)
    assert response["message"] == "File uploaded successfully"


@pytest.mark.asyncio
async def test_upload_file_invalid_file_type():
    file = MagicMock(spec=UploadFile)
    file.content_type = "text/plain"  # Invalid file type
    file.size = 500 * 1000

    with pytest.raises(HTTPException) as exc_info:
        await upload_file(staff_id=1, update_datetime="2024-01-01", file_obj=file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid file type. Supported file types are JPEG, PNG, and PDF"


@pytest.mark.asyncio
async def test_upload_file_exceeds_size():
    file = MagicMock(spec=UploadFile)
    file.content_type = "image/jpeg"
    file.size = 6 * 1000 * 1000  # 6 MB, exceeds 5MB limit

    with pytest.raises(HTTPException) as exc_info:
        await upload_file(staff_id=1, update_datetime="2024-01-01", file_obj=file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "File size exceeds 5MB"


@pytest.mark.asyncio
@patch("src.arrangements.utils.boto3.client")
async def test_delete_file_success(mock_s3_client):
    mock_s3_client.delete_object.return_value = None

    response = await delete_file(staff_id=1, update_datetime="2024-01-01", s3_client=mock_s3_client)
    assert response.status_code == 200
    assert (
        response.body == b'{"message":"File deleted successfully"}'
    )  # Using .body for response content


@pytest.mark.asyncio
@patch("src.arrangements.utils.boto3.client")
async def test_delete_file_failure(mock_s3_client):
    mock_s3_client.delete_object.side_effect = Exception("Delete failed")

    response = await delete_file(staff_id=1, update_datetime="2024-01-01", s3_client=mock_s3_client)
    assert response.status_code == 500
    assert (
        response.body == b'{"message":"An error occurred: Delete failed"}'
    )  # Using .body for response content


@pytest.mark.asyncio
@patch("src.arrangements.utils.boto3.client")
async def test_upload_file_s3_failure(mock_boto_client):
    file = MagicMock(spec=UploadFile)
    file.content_type = "image/jpeg"
    file.size = 500 * 1000  # 500 KB
    file.filename = "test.jpg"
    file.file = BytesIO(b"test file content")  # Mock the file-like object

    # Mock the s3 client and simulate the upload failure
    mock_s3_client = mock_boto_client.return_value

    error_response = {
        "Error": {"Code": "NoSuchBucket", "Message": "The specified bucket does not exist"}
    }
    operation_name = "PutObject"
    mock_s3_client.upload_fileobj.side_effect = ClientError(error_response, operation_name)

    with pytest.raises(ClientError):
        await upload_file(
            staff_id=1, update_datetime="2024-01-01", file_obj=file, s3_client=mock_s3_client
        )


def create_mock_arrangement_response(
    arrangement_id: int = 1,
    update_datetime: datetime = datetime.now(),
    wfh_date: date = date(2024, 1, 1),
) -> ArrangementResponse:
    """Helper function to create a mock ArrangementResponse with all required fields"""
    return ArrangementResponse(
        arrangement_id=arrangement_id,
        update_datetime=update_datetime,
        requester_staff_id=1001,
        wfh_date=wfh_date,
        wfh_type=WfhType.FULL,
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        approving_officer=2001,
        latest_log_id=1,  # Changed from None to valid integer
        delegate_approving_officer=None,
        reason_description=None,
        batch_id=None,
        supporting_doc_1=None,
        supporting_doc_2=None,
        supporting_doc_3=None,
        status_reason=None,
        requester_info=None,
    )


@pytest.mark.asyncio
async def test_create_presigned_url_success():
    with patch("boto3.client") as mock_boto3_client:
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"
        mock_boto3_client.return_value = mock_s3

        result = create_presigned_url("test/file.jpg")

        assert result == "https://presigned-url.com"
        mock_s3.generate_presigned_url.assert_called_once()


@pytest.mark.asyncio
async def test_create_presigned_url_with_none():
    result = create_presigned_url(None)
    assert result is None


@pytest.mark.asyncio
async def test_create_presigned_url_client_error():
    with patch("boto3.client") as mock_boto3_client:
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "InvalidRequest", "Message": "Invalid request"}},
            "generate_presigned_url",
        )
        mock_boto3_client.return_value = mock_s3

        result = create_presigned_url("test/file.jpg")
        assert result is None


def test_compute_pagination_meta():
    arrangements = [create_mock_arrangement_response() for _ in range(6)]
    meta = compute_pagination_meta(arrangements, items_per_page=2, page_num=1)

    assert isinstance(meta, PaginationMeta)
    assert meta.total_count == 6
    assert meta.page_size == 2
    assert meta.page_num == 1
    assert meta.total_pages == 3


def test_format_arrangements_response_with_group():
    # Create a mock arrangement with all required fields
    current_time = datetime.now()
    arrangement = create_mock_arrangement_response(
        arrangement_id=1, update_datetime=current_time, wfh_date=date(2024, 1, 1)
    )
    arrangement.latest_log_id = 1  # Ensure latest_log_id is set

    # Create a group with the arrangement
    group = CreatedArrangementGroupByDate(date="2024-01-01", arrangements=[arrangement])

    result = format_arrangements_response([group])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "date" in result[0]
    assert "pending_arrangements" in result[0]
    assert len(result[0]["pending_arrangements"]) == 1


@pytest.mark.skip("File model not available")
def test_format_arrangements_response_with_all_optional_fields():
    # Skip this test until File model is properly defined
    pass


def test_format_arrangement_response():
    arrangement = create_mock_arrangement_response()
    arrangement.latest_log_id = 1  # Ensure latest_log_id is set
    result = format_arrangement_response(arrangement)

    assert isinstance(result, schemas.ArrangementResponse)
    assert result.arrangement_id == 1
    assert result.requester_staff_id == 1001
    assert result.latest_log_id == 1


def test_format_arrangement_response():
    arrangement = create_mock_arrangement_response()
    result = format_arrangement_response(arrangement)

    assert isinstance(result, schemas.ArrangementResponse)
    assert result.arrangement_id == 1
    assert result.requester_staff_id == 1001
    assert result.wfh_type == WfhType.FULL
    assert result.current_approval_status == ApprovalStatus.PENDING_APPROVAL


def test_compute_pagination_meta_single_page():
    arrangements = [create_mock_arrangement_response()]
    meta = compute_pagination_meta(arrangements, items_per_page=5, page_num=1)
    assert meta.total_pages == 1


def test_compute_pagination_meta_empty_list():
    arrangements = []
    meta = compute_pagination_meta(arrangements, items_per_page=5, page_num=1)
    assert meta.total_count == 0
    assert meta.total_pages == 0


@freezegun.freeze_time("2024-01-01")
def test_get_tomorrow_date():
    result = get_tomorrow_date()
    expected = date(2024, 1, 2)
    assert isinstance(result, date)
    assert result == expected


@pytest.mark.asyncio
async def test_create_presigned_url_empty_string():
    result = create_presigned_url("")
    assert result is None


def test_format_arrangements_response_with_arrangement_list():
    # Create a mock arrangement with all required fields
    arrangement = ArrangementResponse(
        arrangement_id=1,
        update_datetime=datetime.now(),
        requester_staff_id=1001,
        wfh_date=date(2024, 1, 1),
        wfh_type=WfhType.FULL,
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        approving_officer=2001,
        latest_log_id=1,  # Set this to avoid validation error
        delegate_approving_officer=None,
        reason_description=None,
        batch_id=None,
        supporting_doc_1=None,
        supporting_doc_2=None,
        supporting_doc_3=None,
        status_reason=None,
        requester_info=None,
    )

    # Test with a list of ArrangementResponse instead of CreatedArrangementGroupByDate
    result = format_arrangements_response([arrangement])

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], schemas.ArrangementResponse)
    assert result[0].arrangement_id == 1
    assert result[0].requester_staff_id == 1001
    assert result[0].current_approval_status == ApprovalStatus.PENDING_APPROVAL
