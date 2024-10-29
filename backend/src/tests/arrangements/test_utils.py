from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from src.arrangements.utils import (
    delete_file,
    fit_model_to_model,
    fit_model_to_schema,
    fit_schema_to_model,
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


def test_fit_schema_to_model():
    schema = MockSchema(id=1, name="Test")
    model = fit_schema_to_model(schema, MockModel)

    assert model.id == 1
    assert model.name == "Test"


def test_fit_model_to_schema():
    model = {"id": 1, "name": "Test"}
    schema = fit_model_to_schema(model, MockSchema)

    assert schema.id == 1
    assert schema.name == "Test"


def test_fit_model_to_model():
    model_data = MockModel(id=1, name="OldName")
    new_model = fit_model_to_model(model_data, MockModel)

    assert new_model.id == 1
    assert new_model.name == "OldName"


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


def test_fit_schema_to_model_with_field_mapping():
    schema = MockSchema(id=1, name="Test")
    field_mapping = {"name": "name"}
    model = fit_schema_to_model(schema, MockModel, field_mapping)

    assert model.id == 1
    assert model.name == "Test"


def test_fit_model_to_schema_with_field_mapping():
    model = {"id": 1, "name": "Test"}
    field_mapping = {"name": "name"}
    schema = fit_model_to_schema(model, MockSchema, field_mapping)

    assert schema.id == 1
    assert schema.name == "Test"


def test_fit_model_to_model_with_field_mapping():
    model_data = MockModel(id=1, name="OldName")
    field_mapping = {"name": "name"}
    new_model = fit_model_to_model(model_data, MockModel, field_mapping)

    assert new_model.id == 1
    assert new_model.name == "OldName"
