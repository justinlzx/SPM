import os

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..logger import logger


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
