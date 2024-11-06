import os
from copy import deepcopy
from datetime import date, datetime, timedelta
from math import ceil
from typing import List, Union

import boto3
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..logger import logger
from .commons import schemas
from .commons.dataclasses import (
    ArrangementResponse,
    CreateArrangementRequest,
    CreatedArrangementGroupByDate,
    PaginationMeta,
)
from .commons.enums import RecurringFrequencyUnit


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
    object_name = f"{staff_id}/{update_datetime}/{file_obj.filename}"  # Use the original filename

    # Upload the file
    s3_client = boto3.client("s3")
    s3_client.upload_fileobj(
        file_obj.file,  # Use the file-like object directly
        S3_BUCKET_NAME,
        object_name,
        ExtraArgs={
            "Metadata": {
                "staff_id": str(staff_id),
                "update_datetime": str(update_datetime),
            },
            "ContentType": file_obj.content_type,
        },
    )

    logger.info(f"File uploaded successfully: {object_name}")
    return {
        "message": "File uploaded successfully",
        "file_url": object_name,
    }


async def delete_file(staff_id, update_datetime, s3_client):
    """Delete a file from an S3 bucket.

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


async def handle_multi_file_deletion(file_paths: List[str], s3_client):
    for path in file_paths:
        try:
            await delete_file(path, datetime.now(), s3_client)
        except ClientError as delete_error:
            # Log deletion error, but do not raise to avoid overriding the main exception
            logger.info(f"Error deleting file {path} from S3: {str(delete_error)}")


def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object.

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    if object_name:
        # Generate a presigned URL for the S3 object
        s3_client = boto3.client("s3")

        S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
        EXPIRATION = 3600  # 1 hour
        try:
            response = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_NAME, "Key": object_name},
                ExpiresIn=EXPIRATION,
            )
        except ClientError as e:
            logger.error(e)
            return None

        # The response contains the presigned URL
        return response


def expand_recurring_arrangement(
    request: CreateArrangementRequest,
) -> List[CreateArrangementRequest]:
    arrangements_list = [deepcopy(request) for _ in range(request.recurring_occurrences)]

    for i in range(len(arrangements_list)):
        if request.recurring_frequency_unit == RecurringFrequencyUnit.WEEKLY:
            arrangements_list[i].wfh_date = request.wfh_date + relativedelta(
                weeks=i * request.recurring_frequency_number
            )
        else:
            arrangements_list[i].wfh_date = request.wfh_date + relativedelta(
                months=i * request.recurring_frequency_number
            )

    return arrangements_list


def group_arrangements_by_date(
    arrangements: List[ArrangementResponse],
) -> List[CreatedArrangementGroupByDate]:
    arrangements_dict = {}

    logger.info(f"Grouping {len(arrangements)} arrangements by date")

    arrangements.sort(key=lambda x: x.wfh_date, reverse=True)

    for arrangement in arrangements:
        arrangements_dict.setdefault(arrangement.wfh_date.isoformat(), []).append(arrangement)

    result = []
    for key, val in arrangements_dict.items():
        result.append(CreatedArrangementGroupByDate(date=key, arrangements=val))
    logger.info(f"Service: Grouped into {len(result)} dates")
    return result


def compute_pagination_meta(arrangements, items_per_page: int, page_num: int) -> PaginationMeta:
    total_count = len(arrangements)
    total_pages = ceil(total_count / items_per_page)

    return PaginationMeta(
        total_count=total_count,
        page_size=items_per_page,
        page_num=page_num,
        total_pages=total_pages,
    )


def format_arrangements_response(
    arrangements: List[Union[ArrangementResponse, CreatedArrangementGroupByDate]]
) -> List[schemas.ArrangementResponse]:
    if isinstance(arrangements[0], CreatedArrangementGroupByDate):
        response_data = [
            {
                "date": arrangement_date.date,
                "pending_arrangements": [
                    schemas.ArrangementResponse.model_validate(arrangement)
                    for arrangement in arrangement_date.arrangements
                ],
            }
            for arrangement_date in arrangements
        ]
    else:
        response_data = [
            schemas.ArrangementResponse.model_validate(arrangement) for arrangement in arrangements
        ]

    return response_data


def format_arrangement_response(arrangement: ArrangementResponse) -> schemas.ArrangementResponse:
    return schemas.ArrangementResponse.model_validate(arrangement)


def get_tomorrow_date() -> date:
    """Get tomorrow's date at midnight."""
    return datetime.now().date() + timedelta(days=1)
