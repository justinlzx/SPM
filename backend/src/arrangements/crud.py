from typing import List

# from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import models, schemas
from .utils import fit_model_to_model, fit_schema_to_model


def create_recurring_request(db: Session, request: schemas.ArrangementCreate):
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


def create_arrangements(db: Session, arrangements: List[schemas.ArrangementCreate]):
    try:
        created_arrangements_list = []
        for arrangement in arrangements:
            created_arrangement = fit_schema_to_model(arrangement, models.LatestArrangement)
            created_arrangements_list.append(created_arrangement)

        db.add_all(created_arrangements_list)
        db.flush()

        # Create logs for each arrangement and update arrangement with log ID
        for arrangement in created_arrangements_list:
            log = create_request_arrangement_log(db, arrangement)
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


def create_request_arrangement_log(db: Session, arrangement: models.LatestArrangement):
    try:
        arrangement.log_event_type = "request"
        arrangement_log = fit_model_to_model(
            arrangement,
            models.ArrangementLog,
            {"requester_staff_id": "log_event_staff_id", "update_datetime": "log_event_datetime"},
        )
        db.add(arrangement_log)
        db.flush()
        return arrangement_log
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def get_all_arrangements(db: Session):
    try:
        return db.query(models.ArrangementLog).all()
    except SQLAlchemyError as e:
        raise e
