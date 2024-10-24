from datetime import datetime
from typing import List, Literal

# from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from src.employees.models import Employee

from ..logger import logger
from . import models, schemas
from .utils import fit_model_to_model, fit_schema_to_model


def get_arrangement_by_id(db: Session, arrangement_id: int) -> models.LatestArrangement:
    return db.query(models.LatestArrangement).get(arrangement_id)


def get_arrangements_by_staff_ids(
    db: Session,
    staff_ids: List[int],
    current_approval_status: List[
        Literal[
            "pending approval",
            "pending withdrawal",
            "approved",
            "rejected",
            "cancelled",
            "withdrawn",
        ]
    ] = None,
    name: str = None,
    wfh_type: Literal["full", "am", "pm"] = None,
    start_date: datetime = None,
    end_date: datetime = None,
    reason: str = None,
) -> List[schemas.ArrangementCreateResponse]:
    """Fetch the WFH requests for a list of staff IDs with optional filters.

    Args:
        db: Database session
        staff_ids: List of staff IDs to filter by
        current_approval_status: Optional list of approval statuses
        name: Optional employee name filter
        type: Optional arrangement type (full/am/pm)
        start_date: Optional start date filter
        end_date: Optional end date filter
        reason: Optional reason filter
        page_num: Optional page number for pagination

    Returns:
        List of arrangements matching the criteria
    """
    logger.info("Fetching requests by staff ID with filters")
    query = db.query(models.LatestArrangement)
    query = query.join(Employee, Employee.staff_id == models.LatestArrangement.requester_staff_id)
    query = query.filter(models.LatestArrangement.requester_staff_id.in_(staff_ids))

    if name:
        query = query.filter(
            or_(
                Employee.staff_fname.ilike(f"%{name}%"),
                Employee.staff_lname.ilike(f"%{name}%"),
            )
        )
    # Apply optional filters
    if current_approval_status:
        query = query.filter(
            models.LatestArrangement.current_approval_status.in_(current_approval_status)
        )

    if wfh_type:
        query = query.filter(models.LatestArrangement.wfh_type == wfh_type)

    if start_date:
        query = query.filter(func.date(models.LatestArrangement.wfh_date) >= start_date)

    if end_date:
        query = query.filter(func.date(models.LatestArrangement.wfh_date) <= end_date)

    if reason:
        query = query.filter(models.LatestArrangement.reason.ilike(reason))

    result = query.all()

    print(f"Result: {result}")

    return result


def create_arrangement_log(
    db: Session, arrangement: models.LatestArrangement, action: str
) -> models.ArrangementLog:
    print("Entering create_arrangement_log function")
    try:
        print("Calling fit_model_to_model")
        arrangement_log: models.ArrangementLog = fit_model_to_model(
            arrangement,
            models.ArrangementLog,
            {
                "current_approval_status": "approval_status",
            },
        )
        arrangement_log.update_datetime = datetime.utcnow()
        db.add(arrangement_log)
        db.flush()
    except SQLAlchemyError as e:
        print(f"Caught SQLAlchemyError in create_arrangement_log: {str(e)}")
        db.rollback()
        raise e
    return arrangement_log


def create_recurring_request(
    db: Session, request: schemas.ArrangementCreate
) -> models.RecurringRequest:
    try:
        batch = fit_schema_to_model(
            request,
            models.RecurringRequest,
            {"update_datetime": "request_datetime", "wfh_date": "start_date"},
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_arrangements(
    db: Session, arrangements: List[models.LatestArrangement]
) -> List[models.LatestArrangement]:
    try:
        created_arrangements = []
        for arrangement in arrangements:
            # Auto-approve Jack Sim's requests
            if arrangement.requester_staff_id == 130002:
                arrangement.current_approval_status = "approved"

            db.add(arrangement)
            db.flush()
            created_arrangements.append(arrangement)
            created_arrangement_log = create_arrangement_log(db, arrangement, "create")
            arrangement.latest_log_id = created_arrangement_log.log_id
            db.add(created_arrangement_log)
            db.flush()

        db.commit()

        for created_arrangement in created_arrangements:
            db.refresh(created_arrangement)

        return created_arrangements
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_arrangement_approval_status(
    db: Session, arrangement: models.LatestArrangement, action: str
) -> models.LatestArrangement:
    try:
        log = create_arrangement_log(db, arrangement, action)
        arrangement.latest_log_id = log.log_id

        db.commit()
        db.refresh(arrangement)
        return arrangement
    except SQLAlchemyError as e:
        db.rollback()
        raise e
