from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from . import crud, schemas

router = APIRouter()


@router.post("/request")
def create_wfh_request(
    arrangement: schemas.ArrangementCreate, db: Session = Depends(get_db)
):
    try:
        new_arrangement = crud.create_wfh_request(db, arrangement)
        response_data = new_arrangement.__dict__
        response_data.pop("_sa_instance_state", None)

        # TODO: Use Pydantic to perform model validation

        return JSONResponse(
            status_code=201,
            content={
                "message": "Request submitted successfully",
                "data": response_data,
            },
        )

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
