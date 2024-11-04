from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from src.arrangements.commons import dataclasses as dc
from src.arrangements.commons.enums import RecurringFrequencyUnit
from src.arrangements.utils import (
    delete_file,
    expand_recurring_arrangement,
    group_arrangements_by_date,
    upload_file,
)

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
    mock_s3_client.upload_fileobj.side_effect = Exception("S3 upload failed")

    with pytest.raises(HTTPException) as exc_info:
        await upload_file(
            staff_id=1, update_datetime="2024-01-01", file_obj=file, s3_client=mock_s3_client
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "S3 upload failed"


# def test_fit_schema_to_model_with_field_mapping():
#     schema = MockSchema(id=1, name="Test")
#     field_mapping = {"name": "name"}
#     model = fit_schema_to_model(schema, MockModel, field_mapping)

#     assert model.id == 1
#     assert model.name == "Test"


# def test_fit_model_to_schema_with_field_mapping():
#     model = {"id": 1, "name": "Test"}
#     field_mapping = {"name": "name"}
#     schema = fit_model_to_schema(model, MockSchema, field_mapping)

#     assert schema.id == 1
#     assert schema.name == "Test"


# def test_fit_model_to_model_with_field_mapping():
#     model_data = MockModel(id=1, name="OldName")
#     field_mapping = {"name": "name"}
#     new_model = fit_model_to_model(model_data, MockModel, field_mapping)

#     assert new_model.id == 1
#     assert new_model.name == "OldName"
