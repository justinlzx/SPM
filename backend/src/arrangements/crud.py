from datetime import date, datetime
from typing import List, Literal, Optional, Union

# from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from src.employees.models import Employee

from ..logger import logger
from . import models, schemas
from .utils import fit_model_to_model, fit_schema_to_model


def get_arrangement_by_id(db: Session, arrangement_id: int) -> Optional[models.LatestArrangement]:
    return db.query(models.LatestArrangement).get(arrangement_id)


def get_arrangements(
    db: Session,
    staff_ids: Union[int, List[int]],
    current_approval_status: Optional[
        List[
            Literal[
                "pending approval",
                "pending withdrawal",
                "approved",
                "rejected",
                "cancelled",
                "withdrawn",
            ]
        ]
    ] = None,
    name: Optional[str] = None,
    wfh_type: Optional[Literal["full", "am", "pm"]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    reason: Optional[str] = None,
) -> List[models.LatestArrangement]:
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
    staff_ids = list(set(staff_ids)) if isinstance(staff_ids, list) else staff_ids

    # Define the filters
    filters = {
        "current_approval_status": current_approval_status,
        "name": name,
        "wfh_type": wfh_type,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
    }

    # Log the number of staff IDs being fetched
    logger.info(
        f"Crud: Fetching arrangements for {len(staff_ids) if isinstance(staff_ids, list) else 1} staff IDs with filters"
    )

    # Log all non-null filters
    non_null_filters = {key: value for key, value in filters.items() if value}
    logger.info(f"Crud: Applying filters: {non_null_filters}")

    query = db.query(models.LatestArrangement)
    query = query.join(Employee, Employee.staff_id == models.LatestArrangement.requester_staff_id)

    if isinstance(staff_ids, int):
        query = query.filter(models.LatestArrangement.requester_staff_id == staff_ids)
    else:
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
        query = query.filter(models.LatestArrangement.reason_description.like(reason))

    result = query.all()
    logger.info(f"Crud: Found {len(result)} arrangements")

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
            created_arrangement_log: models.ArrangementLog = create_arrangement_log(
                db, arrangement, "create"
            )
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
