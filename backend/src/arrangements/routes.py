from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List


from ..database import get_db
from . import crud, schemas

router = APIRouter()


@router.post("/request")
def create_wfh_request(
    arrangement: schemas.ArrangementCreate, db: Session = Depends(get_db)
):
    try:
        arrangement_requests = []
        if arrangement.is_recurring:
            missing_fields = [
                field
                for field in [
                    "recurring_end_date",
                    "recurring_frequency_number",
                    "recurring_frequency_unit",
                    "recurring_occurrences",
                ]
                if getattr(arrangement, field) is None
            ]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Recurring WFH request requires the following fields to be filled: {', '.join(missing_fields)}",
                )

            for i in range(arrangement.recurring_occurrences):
                arrangement_copy = arrangement.model_copy()

                if arrangement.recurring_frequency_unit == "week":
                    arrangement_copy.wfh_date = (
                        datetime.strptime(arrangement.wfh_date, "%Y-%m-%d")
                        + timedelta(weeks=i * arrangement.recurring_frequency_number)
                    ).strftime("%Y-%m-%d")
                else:
                    arrangement_copy.wfh_date = (
                        datetime.strptime(arrangement.wfh_date, "%Y-%m-%d")
                        + timedelta(days=i * arrangement.recurring_frequency_number * 7)
                    ).strftime("%Y-%m-%d")

                arrangement_requests.append(arrangement_copy)
        else:
            arrangement_requests.append(arrangement)

        response_data = []

        created_arrangements = crud.create_bulk_wfh_request(db, arrangement_requests)

        response_data = [req.__dict__ for req in created_arrangements]
        for data in response_data:
            data.pop("_sa_instance_state", None)

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


@router.get("/view", response_model=List[schemas.ArrangementLog])
def get_all_arrangements(db: Session = Depends(get_db)):
    try:
        arrangements = crud.get_all_arrangements(db)
        return arrangements
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
