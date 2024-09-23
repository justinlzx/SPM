from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import models, schemas


def create_wfh_request(db: Session, arrangement_data: schemas.ArrangementCreate):
    try:
        arrangement = models.ArrangementLog(
            **arrangement_data.model_dump(by_alias=True)
        )
        db.add(arrangement)
        db.commit()
        db.refresh(arrangement)
        return arrangement
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    except ValidationError as e:
        db.rollback()
        raise e
