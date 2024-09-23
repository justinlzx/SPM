from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from .crud import create_arrangement
from .schemas import WFHRequestCreateBody

router = APIRouter()


@router.post("/request")
def create_wfh_request(
    arrangement: WFHRequestCreateBody, db: Session = Depends(get_db)
):
    try:
        new_arrangement = create_arrangement(db, arrangement)
        response_data = new_arrangement.__dict__
        response_data.pop("_sa_instance_state", None)
        response_data["request_created_datetime"] = response_data.pop(
            "last_updated_datetime"
        )

        # TODO: Find a Pydantic native way to perform this conversion and model validation

        return JSONResponse(
            status_code=201,
            content={
                "message": "Arrangement created successfully",
                "data": response_data,
            },
        )

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
