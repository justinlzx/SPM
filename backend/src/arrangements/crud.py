from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import Arrangement
from .schemas import WFHRequestCreateBody


def create_arrangement(db: Session, arrangement_data: WFHRequestCreateBody):
    try:
        arrangement = Arrangement(**arrangement_data.model_dump(by_alias=True))
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
