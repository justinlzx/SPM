from typing import List

# from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import schemas
from .models import LatestArrangement, RecurringRequest, ArrangementLog
from .exceptions import ArrangementActionNotAllowedError, ArrangementNotFoundError
from .utils import fit_model_to_model, fit_schema_to_model
from datetime import datetime


def create_recurring_request(db: Session, request: schemas.ArrangementCreate) -> RecurringRequest:
    try:
        batch = fit_schema_to_model(
            request,
            RecurringRequest,
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
    db: Session, arrangements: List[schemas.ArrangementCreate]
) -> List[LatestArrangement]:
    try:
        created_arrangements_list = []
        for arrangement in arrangements:
            created_arrangement = fit_schema_to_model(arrangement, LatestArrangement)
            created_arrangements_list.append(created_arrangement)

        db.add_all(created_arrangements_list)
        db.flush()

        # Create logs for each arrangement and update arrangement with log ID
        for arrangement in created_arrangements_list:
            log = create_request_arrangement_log(db, arrangement, "create")
            arrangement.latest_log_id = log.log_id  # Update arrangement with log ID
            db.add(arrangement)  # Re-add the updated arrangement to the session

        db.commit()  # Commit both arrangements and logs

        # Refresh all arrangements after commit
        for arrangement in created_arrangements_list:
            db.refresh(arrangement)
        return created_arrangements_list
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_arrangement_approval_status(db: Session, arrangement_id: int, action: str, reason: str):
    try:
        arrangement = db.query(LatestArrangement).get(arrangement_id)

        if not arrangement:
            raise ArrangementNotFoundError(arrangement_id)

        status = {
            "approve": "approved",
            "reject": "rejected",
            "withdraw": "withdrawn",
            "cancel": "cancelled",
        }.get(action)

        if arrangement.current_approval_status != "pending" and action in [
            "approve",
            "reject",
        ]:
            raise ArrangementActionNotAllowedError(arrangement_id, action)

        arrangement.current_approval_status = status
        arrangement.approval_reason = reason

        log = create_request_arrangement_log(db, arrangement, action)
        arrangement.latest_log_id = log.log_id

        db.commit()
        db.refresh(arrangement)
        return arrangement
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_request_arrangement_log(
    db: Session, arrangement: LatestArrangement, action: str
) -> ArrangementLog:
    try:
        arrangement_log = fit_model_to_model(
            arrangement,
            ArrangementLog,
            {
                "current_approval_status": "approval_status",
            },
        )
        arrangement_log.update_datetime = datetime.utcnow()
        arrangement_log.approval_status = arrangement.current_approval_status
        db.add(arrangement_log)
        db.flush()
        return arrangement_log
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def get_all_arrangements(db: Session) -> List[LatestArrangement]:
    try:
        return db.query(LatestArrangement).all()
    except SQLAlchemyError as e:
        raise e


def get_pending_requests_by_staff_ids(db: Session, staff_ids: List[int]):
    """
    Fetch the pending WFH requests for a list of staff IDs.
    """
    try:
        print(f"Fetching pending requests for staff IDs: {staff_ids}")
        results = (
            db.query(LatestArrangement)
            .filter(LatestArrangement.requester_staff_id.in_(staff_ids))
            .all()
        )
        print(f"Retrieved pending requests: {results}")
        return results
    except SQLAlchemyError as e:
        print(f"Error fetching pending requests: {str(e)}")  # Log the error
        return []  # Return an empty list on error
