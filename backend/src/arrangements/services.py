from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from .. import utils
from . import crud, exceptions, models, schemas

STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "withdraw": "withdrawn",
    "cancel": "cancelled",
}


def create_arrangements_from_request(
    db: Session, wfh_request: schemas.ArrangementCreate
) -> List[schemas.ArrangementCreateResponse]:

    if wfh_request.staff_id == 130002:
        wfh_request.current_approval_status = "approved"

    arrangements: List[schemas.ArrangementCreate] = []

    if wfh_request.is_recurring:
        batch: models.RecurringRequest = crud.create_recurring_request(db, wfh_request)
        arrangements: List[schemas.ArrangementCreate] = expand_recurring_arrangement(
            wfh_request, batch.batch_id
        )
    else:
        arrangements.append(wfh_request)

    arrangements_model: List[models.LatestArrangement] = [
        utils.fit_schema_to_model(arrangement, models.LatestArrangement)
        for arrangement in arrangements
    ]

    created_arrangements: List[models.LatestArrangement] = crud.create_arrangements(
        db, arrangements_model
    )

    # Convert to Pydantic model
    # created_arrangements = [req.__dict__ for req in created_arrangements]
    # for data in created_arrangements:
    #     data.pop("_sa_instance_state", None)
    # created_arrangements_schema: schemas.ArrangementCreateResponse = [
    #     utils.fit_model_to_schema(
    #         data,
    #         schemas.ArrangementCreateResponse,
    #         {
    #             "requester_staff_id": "staff_id",
    #             "current_approval_status": "approval_status",
    #         },
    #     )
    #     for data in created_arrangements
    # ]

    # Convert to Pydantic schema
    created_arrangements_schema: List[schemas.ArrangementCreateResponse] = (
        utils.convert_model_to_pydantic_schema(
            created_arrangements, schemas.ArrangementCreateResponse
        )
    )

    return created_arrangements_schema


def expand_recurring_arrangement(
    wfh_request: schemas.ArrangementCreate, batch_id: int
) -> List[schemas.ArrangementCreate]:
    arrangements_list: List[schemas.ArrangementCreate] = []

    for i in range(wfh_request.recurring_occurrences):
        arrangement_copy: schemas.ArrangementCreate = wfh_request.model_copy()

        if wfh_request.recurring_frequency_unit == "week":
            arrangement_copy.wfh_date = (
                datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                + timedelta(weeks=i * wfh_request.recurring_frequency_number)
            ).strftime("%Y-%m-%d")
        else:
            arrangement_copy.wfh_date = (
                datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                + timedelta(days=i * wfh_request.recurring_frequency_number * 7)
            ).strftime("%Y-%m-%d")

        arrangement_copy.batch_id = batch_id

        arrangements_list.append(arrangement_copy)

    return arrangements_list


def get_arrangement_by_id(db: Session, arrangement_id: int) -> models.LatestArrangement:
    arrangement: models.LatestArrangement = crud.get_arrangement_by_id(db, arrangement_id)

    if not arrangement:
        raise exceptions.ArrangementNotFoundError(arrangement_id)

    return arrangement


def update_arrangement_approval_status(
    db: Session, wfh_update: schemas.ArrangementUpdate
) -> schemas.ArrangementUpdate:

    wfh_update.reason_description = (
        "[DEFAULT] Approved by Manager"
        if wfh_update.reason_description is None
        else wfh_update.reason_description
    )

    arrangement: models.LatestArrangement = crud.get_arrangement_by_id(
        db, wfh_update.arrangement_id
    )

    if not arrangement:
        raise exceptions.ArrangementNotFoundError(wfh_update.arrangement_id)

    # TODO: Add logic for raising ArrangementActionNotAllowed exceptions based on the current status

    arrangement.current_approval_status = STATUS.get(wfh_update.action)
    arrangement.approving_officer = wfh_update.approving_officer
    arrangement.reason_description = wfh_update.reason_description

    arrangement: models.LatestArrangement = crud.update_arrangement_approval_status(
        db, arrangement, wfh_update.action
    )

    arrangement_schema = schemas.ArrangementUpdate(**arrangement.__dict__, action=wfh_update.action)

    return arrangement_schema
