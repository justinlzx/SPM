from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from .. import utils
from ..employees import exceptions as employee_exceptions
from ..employees import models as employee_models
from ..employees import services as employee_services
from . import crud, exceptions, models

from .schemas import (
    ArrangementCreate,
    ArrangementCreateResponse,
    ArrangementResponse,
    ArrangementUpdate,
)

from .models import LatestArrangement

STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "withdraw": "withdrawn",
    "cancel": "cancelled",
}


def get_arrangement_by_id(db: Session, arrangement_id: int) -> LatestArrangement:
    arrangement: LatestArrangement = crud.get_arrangement_by_id(db, arrangement_id)

    if not arrangement:
        raise exceptions.ArrangementNotFoundError(arrangement_id)

    return arrangement


def get_personal_arrangements_by_filter(
    db: Session, staff_id: int, current_approval_status: List[str]
) -> List[ArrangementResponse]:

    arrangements: List[models.LatestArrangement] = crud.get_arrangements_by_filter(
        db, staff_id, current_approval_status
    )
    arrangements_schema: List[ArrangementResponse] = (
        utils.convert_model_to_pydantic_schema(arrangements, ArrangementResponse)
    )

    return arrangements_schema


def get_subordinates_arrangements(
    db: Session, manager_id: int, current_approval_status: List[str]
) -> List[ArrangementResponse]:

    # Check if the employee is a manager
    employees_under_manager: List[employee_models.Employee] = (
        employee_services.get_subordinates_by_manager_id(db, manager_id)
    )

    if not employees_under_manager:
        raise employee_exceptions.ManagerNotFoundException(manager_id)

    employees_under_manager_ids = [
        employee.staff_id for employee in employees_under_manager
    ]

    arrangements = crud.get_arrangements_by_staff_ids(
        db, employees_under_manager_ids, current_approval_status
    )

    arrangements_schema: List[ArrangementResponse] = (
        utils.convert_model_to_pydantic_schema(arrangements, ArrangementResponse)
    )

    return arrangements_schema


def get_team_arrangements(
    db: Session, staff_id: int, current_approval_status: List[str]
) -> Dict[str, List[ArrangementResponse]]:

    arrangements: Dict[str, List[ArrangementResponse]] = {}

    # Get arrangements of peer employees
    # TODO: Exception handling and testing
    peer_employees: List[employee_models.Employee] = (
        employee_services.get_peers_by_staff_id(db, staff_id)
    )
    peer_arrangements: List[models.LatestArrangement] = (
        crud.get_arrangements_by_staff_ids(
            db, [peer.staff_id for peer in peer_employees], current_approval_status
        )
    )
    peer_arrangements: List[ArrangementResponse] = (
        utils.convert_model_to_pydantic_schema(peer_arrangements, ArrangementResponse)
    )

    arrangements["peers"] = peer_arrangements

    try:
        # If employee is manager, get arrangements of subordinates
        subordinates_arrangements: List[models.LatestArrangement] = (
            get_subordinates_arrangements(db, staff_id, current_approval_status)
        )

        subordinates_arrangements: List[ArrangementResponse] = (
            utils.convert_model_to_pydantic_schema(
                subordinates_arrangements, ArrangementResponse
            )
        )
        arrangements["subordinates"] = subordinates_arrangements
    except employee_exceptions.ManagerNotFoundException:
        pass
    return arrangements


def create_arrangements_from_request(
    db: Session, wfh_request: ArrangementCreate
) -> List[ArrangementCreateResponse]:

    # Auto Approve Jack Sim's requests
    if wfh_request.staff_id == 130002:
        wfh_request.current_approval_status = "approved"

    arrangements: List[ArrangementCreate] = []

    if wfh_request.is_recurring:
        batch: models.RecurringRequest = crud.create_recurring_request(db, wfh_request)
        arrangements: List[ArrangementCreate] = expand_recurring_arrangement(
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
    # created_arrangements_schema: ArrangementCreateResponse = [
    #     utils.fit_model_to_schema(
    #         data,
    #         ArrangementCreateResponse,
    #         {
    #             "requester_staff_id": "staff_id",
    #             "current_approval_status": "approval_status",
    #         },
    #     )
    #     for data in created_arrangements
    # ]

    # Convert to Pydantic schema
    created_arrangements_schema: List[ArrangementCreateResponse] = (
        utils.convert_model_to_pydantic_schema(
            created_arrangements, ArrangementCreateResponse
        )
    )

    return created_arrangements_schema


def expand_recurring_arrangement(
    wfh_request: ArrangementCreate, batch_id: int
) -> List[ArrangementCreate]:
    arrangements_list: List[ArrangementCreate] = []

    for i in range(wfh_request.recurring_occurrences):
        arrangement_copy: ArrangementCreate = wfh_request.model_copy()

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

        # Auto Approve Jack Sim's requests
        if arrangement_copy.staff_id == 130002:
            arrangement_copy.current_approval_status = "approved"

        arrangements_list.append(arrangement_copy)

    return arrangements_list


def update_arrangement_approval_status(
    db: Session, wfh_update: ArrangementUpdate
) -> ArrangementUpdate:

    # TODO: Check that the approving officer is the manager of the employee

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

    arrangement_schema = ArrangementUpdate(
        **arrangement.__dict__, action=wfh_update.action
    )

    return arrangement_schema
