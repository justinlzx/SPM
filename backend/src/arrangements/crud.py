from typing import List

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import models, schemas


def create_bulk_wfh_request(
    db: Session, arrangements_data: List[schemas.ArrangementCreate]
):
    try:
        batch_id = None

        if len(arrangements_data) > 1:
            batch = models.ArrangementBatch(
                update_datetime=arrangements_data[0].update_datetime,
                requester_staff_id=arrangements_data[0].requester_staff_id,
                start_date=arrangements_data[0].wfh_date,
                end_date=arrangements_data[0].recurring_end_date,
                recurring_frequency_number=arrangements_data[
                    0
                ].recurring_frequency_number,
                recurring_frequency_unit=arrangements_data[0].recurring_frequency_unit,
                recurring_occurrences=arrangements_data[0].recurring_occurrences,
                wfh_type=arrangements_data[0].wfh_type,
                reason_description=arrangements_data[0].reason_description,
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

            batch_id = batch.batch_id

        arrangements = []
        for arrangement_data in arrangements_data:
            arrangement_dict = arrangement_data.model_dump(by_alias=True)
            # Remove invalid fields
            valid_fields = {
                key: value
                for key, value in arrangement_dict.items()
                if key in models.ArrangementLog.__table__.columns
            }
            valid_fields["batch_id"] = batch_id
            arrangement = models.ArrangementLog(**valid_fields)
            arrangements.append(arrangement)
        db.add_all(arrangements)
        db.commit()
        for arrangement in arrangements:
            db.refresh(arrangement)
        return arrangements
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    except ValidationError as e:
        db.rollback()
        raise e


def get_all_arrangements(db: Session):
    try:
        return db.query(models.ArrangementLog).all()
    except SQLAlchemyError as e:
        raise e
