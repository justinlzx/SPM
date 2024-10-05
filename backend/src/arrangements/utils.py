from io import BytesIO
from typing import Dict

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta

import logging
from botocore.exceptions import ClientError

# from ..s3 import s3_client
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


async def upload_file(staff_id, arrangement_id, file_obj):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # TODO: change this to get the staff_id and arrangement_id from the request
    staff_id = 1
    arrangement_id = 1

    # Read the file content and convert to BytesIO
    file_content = await file_obj.read()
    file_obj = BytesIO(file_content)

    S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    OBJECT_NAME = f"{staff_id}/{arrangement_id}/{file_obj}"

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            OBJECT_NAME,
            ExtraArgs={
                "Metadata": {
                    "staff_id": str(staff_id),
                    "arrangement_id": str(arrangement_id),
                }
            },
        )
        if not response:
            raise HTTPException(status_code=500, detail="File upload failed")

        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "filename": file_obj.filename,
            },
        )
    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=500, detail=str(e))
