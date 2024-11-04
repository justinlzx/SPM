from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from src.notifications.email_notifications import craft_and_send_auto_rejection_email

from ..database import get_db
from ..employees import exceptions as employee_exceptions
from ..logger import logger
from ..notifications import exceptions as notification_exceptions
from ..schemas import JSendResponse, PaginationMeta
from . import services
from .commons import dataclasses as dc
from .commons import schemas
from .commons.enums import ApprovalStatus
from .commons.exceptions import (
    ArrangementActionNotAllowedException,
    ArrangementNotFoundException,
    S3UploadFailedException,
)
from .utils import format_arrangement_response, format_arrangements_response

router = APIRouter()


@router.get("/", summary="Get all arrangements with optional filters")
def get_arrangements(
    db: Session = Depends(get_db),
    request_filters: schemas.ArrangementFilters = Depends(schemas.ArrangementFilters.as_query),
) -> JSendResponse:
    try:
        # Convert to dataclasses
        filters = dc.ArrangementFilters.from_dict(request_filters.model_dump())

        # Get arrangements
        logger.info("Route: Fetching all arrangements")
        data = services.get_all_arrangements(db, filters)
        logger.info(f"Route: Found {len(data)} arrangements")

        # Convert to Pydantic model
        response_data = format_arrangements_response(data)

        return JSendResponse(
            status="success",
            data=response_data,
        )
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{arrangement_id}", summary="Get an arrangement by its arrangement_id")
def get_arrangement_by_id(arrangement_id: int, db: Session = Depends(get_db)) -> JSendResponse:
    try:
        # Get arrangement
        logger.info(f"Route: Fetching arrangement with ID: {arrangement_id}")
        data = services.get_arrangement_by_id(db, arrangement_id)
        logger.info("Route: Found arrangement")

        # Convert to Pydantic model
        response_data = format_arrangement_response(data)

        return JSendResponse(
            status="success",
            data=response_data,
        )
    except ArrangementNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/personal/{staff_id}",
    summary="Get personal arrangements by an employee's staff_id",
)
def get_personal_arrangements(
    staff_id: int,
    current_approval_status: Optional[List[ApprovalStatus]] = Query(None),
    db: Session = Depends(get_db),
) -> JSendResponse:
    try:
        # Get arrangements
        logger.info(f"Route: Fetching personal arrangements for staff ID: {staff_id}")
        data = services.get_personal_arrangements(
            db=db,
            staff_id=staff_id,
            current_approval_status=current_approval_status,
        )
        logger.info(f"Route: Found {len(data)} arrangements for staff ID {staff_id}")

        # Convert to Pydantic model
        response_data = format_arrangements_response(data)

        return JSendResponse(
            status="success",
            data=response_data,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/subordinates/{manager_id}",
    summary="Get arrangements for subordinate employees under a manager",
)
def get_subordinates_arrangements(
    manager_id: int,
    request_filters: schemas.ArrangementFilters = Depends(schemas.ArrangementFilters.as_query),
    request_pagination: schemas.PaginationConfig = Depends(schemas.PaginationConfig.as_query),
    db: Session = Depends(get_db),
) -> JSendResponse:
    try:
        # Convert to dataclasses
        filters = dc.ArrangementFilters.from_dict(request_filters.model_dump())
        pagination = dc.PaginationConfig.from_dict(request_pagination.model_dump())

        # Get arrangements
        logger.info(f"Fetching arrangements for employees under manager ID: {manager_id}")
        data, pagination_meta = services.get_subordinates_arrangements(
            db=db, manager_id=manager_id, filters=filters, pagination=pagination
        )
        if filters.group_by_date:
            logger.info(f"Route: Found {pagination_meta.total_count} dates")
        else:
            logger.info(f"Route: Found {pagination_meta.total_count} arrangements")

        # Convert to Pydantic model
        response_data = format_arrangements_response(data)
        response_pagination_meta = PaginationMeta.model_validate(pagination_meta)

        return JSendResponse(
            status="success",
            data=response_data,
            pagination_meta=response_pagination_meta,
        )
    except employee_exceptions.ManagerWithIDNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/team/{staff_id}",
    summary="Get all arrangements for a team, including peers and subordinates",
)
def get_team_arrangements(
    staff_id: int,
    request_filters: schemas.ArrangementFilters = Depends(schemas.ArrangementFilters.as_query),
    request_pagination: schemas.PaginationConfig = Depends(schemas.PaginationConfig.as_query),
    db: Session = Depends(get_db),
) -> JSendResponse:
    try:
        # Convert to dataclasses
        filters = dc.ArrangementFilters.from_dict(request_filters.model_dump())
        pagination = dc.PaginationConfig.from_dict(request_pagination.model_dump())

        # Get arrangements
        logger.info(f"Route: Fetching arrangements for team of staff ID: {staff_id}")
        data, pagination_meta = services.get_team_arrangements(db, staff_id, filters, pagination)
        if filters.group_by_date:
            logger.info(f"Route: Found {pagination_meta.total_count} dates")
        else:
            logger.info(f"Route: Found {pagination_meta.total_count} arrangements")

        # Convert to Pydantic model
        response_data = format_arrangements_response(data)
        response_pagination_meta = PaginationMeta.model_validate(pagination_meta)

        return JSendResponse(
            status="success",
            data=response_data,
            pagination_meta=response_pagination_meta,
        )
    except ArrangementNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/logs/all", summary="Get all arrangement logs")
def get_arrangement_logs(db: Session = Depends(get_db)) -> JSendResponse:
    try:
        logger.info("Route: Fetching arrangement logs")
        data = services.get_arrangement_logs(db)
        logger.info(f"Route: Found {len(data)} logs")

        arrangement_logs = [schemas.ArrangementLogResponse.model_validate(log) for log in data]

        return JSendResponse(
            status="success",
            data=arrangement_logs,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request")
async def create_wfh_request(
    request: schemas.CreateArrangementRequest = Depends(schemas.CreateArrangementRequest.as_form),
    supporting_docs: Annotated[Optional[List[UploadFile]], File()] = [],
    db: Session = Depends(get_db),
) -> JSendResponse:
    try:
        # Convert to dataclasses
        wfh_request = dc.CreateArrangementRequest(
            update_datetime=datetime.now(),
            current_approval_status=ApprovalStatus.PENDING_APPROVAL,
            **request.model_dump(),
        )

        # Create arrangements
        arrangements = await services.create_arrangements_from_request(
            db, wfh_request, supporting_docs
        )

        # Convert to Pydantic model
        response_data = format_arrangements_response(arrangements)

        return JSendResponse(
            status="success",
            data=response_data,
        )
    except S3UploadFailedException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{arrangement_id}/status", summary="Update the status of a WFH request")
async def update_wfh_request(
    arrangement_id: int,
    update: schemas.UpdateArrangementRequest = Depends(schemas.UpdateArrangementRequest.as_form),
    supporting_docs: Annotated[Optional[List[UploadFile]], File()] = None,
    db: Session = Depends(get_db),
) -> JSendResponse:
    try:
        # Convert to dataclasses
        wfh_update = dc.UpdateArrangementRequest(
            update_datetime=datetime.now(),
            arrangement_id=arrangement_id,
            **update.model_dump(),
        )

        # Update arrangements
        updated_arrangement = await services.update_arrangement_approval_status(
            db, wfh_update, supporting_docs
        )

        # TODO: REVIEW deleted lines for skip employee lookup for cancel and withdrawn
        # Convert to Pydantic model
        response_data = format_arrangement_response(updated_arrangement)

        return JSendResponse(
            status="success",
            data=response_data,
        )

    except ArrangementNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ArrangementActionNotAllowedException as e:
        raise HTTPException(status_code=406, detail=str(e))

    except notification_exceptions.EmailNotificationException as e:
        raise HTTPException(status_code=500, detail=str(e))

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")  # Log the database error
        raise HTTPException(status_code=500, detail="Database error")


# FOR JOSHUA!!!! DELETE WHEN NOT NEEDED ANYMORE
@router.post(
    "/{arrangement_id}/forjosh/auto-reject-email",
    summary="Send auto-rejection email for an arrangement",
)
async def send_auto_reject_email(
    arrangement_id: int, db: Session = Depends(get_db)
) -> JSendResponse:
    try:
        logger.info(f"Route: Sending auto-rejection email for arrangement ID: {arrangement_id}")
        await craft_and_send_auto_rejection_email(arrangement_id, db)

        return JSendResponse(
            status="success",
            data={"message": f"Auto-rejection email sent for arrangement {arrangement_id}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except notification_exceptions.EmailNotificationException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
