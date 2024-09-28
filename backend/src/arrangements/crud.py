from typing import List, Optional

# from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import schemas
from .models import LatestArrangement, RecurringRequest, ArrangementLog
from .exceptions import ArrangementActionNotAllowedError, ArrangementNotFoundError
from .utils import fit_model_to_model, fit_schema_to_model


def create_recurring_request(
    db: Session, request: schemas.ArrangementCreate
) -> RecurringRequest:
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


def update_arrangement_approval_status(
    db: Session, arrangement_id: int, action: str, reason: str
):
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
                "requester_staff_id": "log_event_staff_id",
                "update_datetime": "log_event_datetime",
            },
        )
        arrangement_log.log_event_type = action
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


def get_arrangements_by_manager(
    db: Session, manager_id: int, status: Optional[str] = None
):

    try:
        query = db.query(ArrangementLog).where(
            ArrangementLog.approving_officer == manager_id
        )

        # if status is empty, then it will get all arrangements
        if status:
            query = query.where(ArrangementLog.approval_status == status)
        return query.all()
    except SQLAlchemyError as e:
        raise e
