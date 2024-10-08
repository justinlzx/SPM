from datetime import datetime
from typing import List

# from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import models, schemas
from .utils import fit_model_to_model, fit_schema_to_model


def get_arrangement_by_id(db: Session, arrangement_id: int) -> models.LatestArrangement:
    return db.query(models.LatestArrangement).get(arrangement_id)


def get_arrangements_by_filter(
    db: Session,
    requester_staff_id: int = None,
    current_approval_status: List[str] = None,
) -> List[models.LatestArrangement]:
    query = db.query(models.LatestArrangement)

    if requester_staff_id:
        query = query.filter(
            models.LatestArrangement.requester_staff_id == requester_staff_id
        )
    if current_approval_status:
        if len(current_approval_status) > 1:
            query = query.filter(
                models.LatestArrangement.current_approval_status.in_(
                    current_approval_status
                )
            )
        else:
            query = query.filter(
                models.LatestArrangement.current_approval_status
                == current_approval_status[0]
            )

    return query.all()


def get_arrangements_by_staff_ids(
    db: Session, staff_ids: List[int], current_approval_status: List[str] = None
) -> List[models.LatestArrangement]:
    """Fetch the WFH requests for a list of staff IDs."""
    print(f"Fetching pending requests for staff IDs: {staff_ids}")
    query = db.query(models.LatestArrangement)
    query = query.filter(models.LatestArrangement.requester_staff_id.in_(staff_ids))

    if current_approval_status:
        if len(current_approval_status) > 1:
            query = query.filter(
                models.LatestArrangement.current_approval_status.in_(
                    current_approval_status
                )
            )
        else:
            query = query.filter(
                models.LatestArrangement.current_approval_status
                == current_approval_status[0]
            )

    # print(f"Retrieved pending requests: {results}")
    return query.all()


def create_arrangement_log(
    db: Session, arrangement: models.LatestArrangement, action: str
) -> models.ArrangementLog:
    try:
        arrangement_log: models.ArrangementLog = fit_model_to_model(
            arrangement,
            models.ArrangementLog,
            {
                "current_approval_status": "approval_status",
            },
        )
        arrangement_log.update_datetime = datetime.utcnow()

        # arrangement_log.approval_status = arrangement.current_approval_status
        db.add(arrangement_log)
        db.flush()
        return arrangement_log
    except SQLAlchemyError as e:
        db.rollback()
        raise e


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
