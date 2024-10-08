from io import BytesIO
from typing import Dict

from fastapi import HTTPException
from ..logger import logger
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta

import boto3
import os


def fit_schema_to_model(
    schema_data: BaseModel,
    model_type: DeclarativeMeta,
    field_mapping: Dict[str, str] = None,
):
    """Transforms a Pydantic schema instance into a SQLAlchemy model instance.

    Args:
        schema_data (BaseModel): An instance of a Pydantic schema.
        model_type (DeclarativeMeta): The SQLAlchemy model class to transform the schema into.
        field_mapping (Dict[str, str], optional): A dictionary mapping schema field names to model
        field names. Defaults to None.

    Returns:
        model_type: An instance of the SQLAlchemy model populated with data from the schema.
    """
    if field_mapping is None:
        field_mapping = {}

    data_dict = schema_data.model_dump(by_alias=True)
    # Remove invalid fields
    valid_fields = {
        field_mapping.get(key, key): value
        for key, value in data_dict.items()
        if field_mapping.get(key, key) in model_type.__table__.columns
    }
    model_data = model_type(**valid_fields)
    return model_data


def fit_model_to_schema(
    model_data: DeclarativeMeta,
    schema_type: BaseModel,
    field_mapping: Dict[str, str] = None,
):
    """Transforms a SQLAlchemy model instance into a Pydantic schema instance.

    Args:
        model_data (DeclarativeMeta): An instance of a SQLAlchemy model.
        schema_type (BaseModel): The Pydantic schema class to transform the model into.
        field_mapping (Dict[str, str], optional): A dictionary mapping model field names to schema
        field names. Defaults to None.

    Returns:
        schema_type: An instance of the Pydantic schema populated with data from the model.
    """
    if field_mapping is None:
        field_mapping = {}

    # Remove invalid fields
    valid_fields = {
        field_mapping.get(key, key): value
        for key, value in model_data.items()
        if field_mapping.get(key, key) in schema_type.model_fields
    }

    schema_data = schema_type(**valid_fields)
    return schema_data


def fit_model_to_model(
    model_data: DeclarativeMeta,
    model_type: DeclarativeMeta,
    field_mapping: Dict[str, str] = None,
):
    if field_mapping is None:
        field_mapping = {}

    # Remove invalid fields
    valid_fields = {
        field_mapping.get(key, key): value
        for key, value in model_data.__dict__.items()
        if field_mapping.get(key, key) in model_type.__table__.columns
    }
    model_data = model_type(**valid_fields)
    return model_data


async def upload_file(staff_id, update_datetime, file_obj, s3_client=None):
    FILE_TYPE = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file_obj.content_type not in FILE_TYPE:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported file types are JPEG, PNG, and PDF",
        )

    # Check file size before reading content
    MB = 1000 * 1000
    if file_obj.size > 5 * MB:  # Assuming file_obj has a 'size' attribute
        raise HTTPException(status_code=400, detail="File size exceeds 5MB")

    S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    object_name = (
        f"{staff_id}/{update_datetime}/{file_obj.filename}"  # Use the original filename
    )

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_fileobj(
            file_obj.file,  # Use the file-like object directly
            S3_BUCKET_NAME,
            object_name,
            ExtraArgs={
                "Metadata": {
                    "staff_id": str(staff_id),
                    "update_datetime": str(update_datetime),
                }
            },
        )

        # file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{OBJECT_NAME}"

        logger.info(f"File uploaded successfully: {object_name}")
        return {
            "message": "File uploaded successfully",
            "file_url": object_name,
        }
    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=500, detail=str(e))


async def delete_file(staff_id, update_datetime, s3_client=None):
    """Delete a file from an S3 bucket

    :param bucket: Bucket to delete from
    :return: True if file was deleted, else False
    """

    S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    FILE_PATH = f"{staff_id}/{update_datetime}"
    logger.info(f"Deleting file: {FILE_PATH}")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=FILE_PATH)

        logger.info(f"File deleted successfully: {FILE_PATH}")
        return JSONResponse(
            status_code=200,
            content={"message": "File deleted successfully"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"An error occurred: {str(e)}"},
        )
