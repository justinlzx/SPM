from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Dict, List

import boto3
from fastapi import File
from sqlalchemy.orm import Session

from src.employees.schemas import EmployeeBase
from ..logger import logger

from src.arrangements.utils import delete_file, upload_file
from src.employees.crud import get_employee_by_staff_id
from src.notifications.email_notifications import fetch_manager_info

from .. import utils
from .utils import create_presigned_url
from ..employees import exceptions as employee_exceptions
from ..employees import models as employee_models
from ..employees import services as employee_services
from . import crud, exceptions, models

from .schemas import (
    ArrangementCreate,
    ArrangementCreateResponse,
    ArrangementCreateWithFile,
    ArrangementResponse,
    ArrangementUpdate,
    ManagerPendingRequestResponse,
    ManagerPendingRequests,
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
    arrangements_schema: List[ArrangementResponse] = utils.convert_model_to_pydantic_schema(
        arrangements, ArrangementResponse
    )

    return arrangements_schema


def get_subordinates_arrangements(
    db: Session, manager_id: int, current_approval_status: List[str]
) -> List[ManagerPendingRequestResponse]:

    # Check if the employee is a manager
    employees_under_manager: List[employee_models.Employee] = (
        employee_services.get_subordinates_by_manager_id(db, manager_id)
    )

    if not employees_under_manager:
        raise employee_exceptions.ManagerNotFoundException(manager_id)

    employees_under_manager_ids = [employee.staff_id for employee in employees_under_manager]

    arrangements = crud.get_arrangements_by_staff_ids(
        db, employees_under_manager_ids, current_approval_status
    )

    arrangements_schema: List[ArrangementCreateResponse] = (
        utils.convert_model_to_pydantic_schema(arrangements, ArrangementCreateResponse)


    # get presigned url for each supporting document in each arrangement
    arrangements_schema = [
        ArrangementCreateResponse(
            **{
                **arrangement.model_dump(),
                "supporting_doc_1": (
                    create_presigned_url(arrangement.supporting_doc_1)
                    if arrangement.supporting_doc_1
                    else None
                ),
                "supporting_doc_2": (
                    create_presigned_url(arrangement.supporting_doc_2)
                    if arrangement.supporting_doc_2
                    else None
                ),
                "supporting_doc_3": (
                    create_presigned_url(arrangement.supporting_doc_3)
                    if arrangement.supporting_doc_3
                    else None
                ),
            }
        )
        for arrangement in arrangements_schema
    ]
    arrangements_by_employee = group_arrangements_by_employee(arrangements_schema)
    return arrangements_by_employee


def group_arrangements_by_employee(
    arrangements_schema: List[ArrangementCreateResponse],
) -> List[ManagerPendingRequests]:

    arrangements_dict = {}

    for arrangement in arrangements_schema:
        staff_id = arrangement.staff_id
        if staff_id not in arrangements_dict:
            arrangements_dict[staff_id] = []

        arrangements_dict[staff_id].append(arrangement)

    result = []
    for _, val in arrangements_dict.items():
        result.append(
            ManagerPendingRequests(
                employee=val[0].requester_info, pending_arrangements=val
            )
        )

    return result


def get_team_arrangements(
    db: Session, staff_id: int, current_approval_status: List[str]
) -> Dict[str, List[ArrangementResponse]]:

    arrangements: Dict[str, List[ArrangementResponse]] = {}

    # Get arrangements of peer employees
    # TODO: Exception handling and testing
    peer_employees: List[employee_models.Employee] = employee_services.get_peers_by_staff_id(
        db, staff_id
    )
    peer_arrangements: List[models.LatestArrangement] = crud.get_arrangements_by_staff_ids(
        db, [peer.staff_id for peer in peer_employees], current_approval_status
    )
    peer_arrangements: List[ArrangementResponse] = utils.convert_model_to_pydantic_schema(
        peer_arrangements, ArrangementResponse
    )

    arrangements["peers"] = peer_arrangements

    try:
        # If employee is manager, get arrangements of subordinates
        subordinates_arrangements: List[models.LatestArrangement] = get_subordinates_arrangements(
            db, staff_id, current_approval_status
        )

        subordinates_arrangements: List[ArrangementResponse] = (
            utils.convert_model_to_pydantic_schema(subordinates_arrangements, ArrangementResponse)
        )
        arrangements["subordinates"] = subordinates_arrangements
    except employee_exceptions.ManagerNotFoundException:
        pass
    return arrangements


async def create_arrangements_from_request(
    db: Session,
    wfh_request: ArrangementCreate,
    supporting_docs: List[File] = File(None),
) -> List[ArrangementCreateResponse]:

    s3_client = boto3.client("s3")
    file_paths = []
    created_arrangements = []

    try:
        # Auto Approve Jack Sim's requests
        wfh_request = ArrangementCreateWithFile.model_validate(wfh_request)

        if wfh_request.staff_id == 130002:
            wfh_request.current_approval_status = "approved"

        # Fetch employee (staff) information
        staff = get_employee_by_staff_id(db, wfh_request.staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Fetch manager info using the helper function from notifications
        manager_info = await fetch_manager_info(wfh_request.staff_id)
        manager = None

        # Only fetch manager if manager_id is not null
        if (
            manager_info
            and manager_info["manager_id"] is not None
            and manager_info["manager_id"] != wfh_request.staff_id
        ):
            manager = get_employee_by_staff_id(db, manager_info["manager_id"])

        wfh_request.approving_officer = manager.staff_id if manager else None
        # Upload supporting documents to S3 bucket
        for file in supporting_docs:
            response = await upload_file(
                wfh_request.staff_id,
                str(wfh_request.update_datetime),
                file,
                s3_client,
            )

            if not response:
                raise Exception(f"Failed to upload supporting document: {file}")

            file_paths.append(response["file_url"])

        wfh_request.supporting_doc_1 = file_paths[0] if file_paths else None
        wfh_request.supporting_doc_2 = file_paths[1] if len(file_paths) > 1 else None
        wfh_request.supporting_doc_3 = file_paths[2] if len(file_paths) > 2 else None

        arrangements: List[ArrangementCreateWithFile] = []

        if wfh_request.is_recurring:
            batch: models.RecurringRequest = crud.create_recurring_request(db, wfh_request)
            arrangements: List[ArrangementCreateWithFile] = expand_recurring_arrangement(
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

        # Convert to Pydantic schema
        created_arrangements_schema: List[ArrangementCreateResponse] = (
            utils.convert_model_to_pydantic_schema(created_arrangements, ArrangementCreateResponse)
        )

        return created_arrangements_schema

    except Exception as upload_error:
        # If any error occurs, delete uploaded files from S3
        logger.info(f"Deleting files due to error: {str(upload_error)}")
        if file_paths:
            for path in file_paths:
                try:
                    await delete_file(path, s3_client)
                except Exception as e:
                    # Log deletion error, but do not raise to avoid overriding the main exception
                    logger.info(f"Error deleting file {path} from S3: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading files: {str(upload_error)}",
        )


def expand_recurring_arrangement(
    wfh_request: ArrangementCreateWithFile, batch_id: int
) -> List[ArrangementCreateWithFile]:
    arrangements_list: List[ArrangementCreateWithFile] = []

    for i in range(wfh_request.recurring_occurrences):
        arrangement_copy: ArrangementCreateWithFile = wfh_request.model_copy()

        if wfh_request.recurring_frequency_unit == "week":
            arrangement_copy.wfh_date = (
                datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                + timedelta(weeks=i * wfh_request.recurring_frequency_number)
            ).strftime("%Y-%m-%d")
        elif wfh_request.recurring_frequency_unit == "month":
            arrangement_copy.wfh_date = (
                datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
                + relativedelta(months=i * wfh_request.recurring_frequency_number)
            ).strftime("%Y-%m-%d")

        arrangement_copy.batch_id = batch_id
        # Auto Approve Jack Sim's requests
        if arrangement_copy.staff_id == 130002:
            arrangement_copy.current_approval_status = "approved"

        arrangements_list.append(arrangement_copy)

    return arrangements_list


# def expand_recurring_arrangement(
#     wfh_request: ArrangementCreateWithFile, batch_id: int
# ) -> List[ArrangementCreateWithFile]:
#     arrangements_list: List[ArrangementCreateWithFile] = []

#     for i in range(wfh_request.recurring_occurrences):
#         arrangement_copy: ArrangementCreateWithFile = wfh_request.model_copy()

#         if wfh_request.recurring_frequency_unit == "week":
#             arrangement_copy.wfh_date = (
#                 datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
#                 + timedelta(weeks=i * wfh_request.recurring_frequency_number)
#             ).strftime("%Y-%m-%d")
#         else:
#             arrangement_copy.wfh_date = (
#                 datetime.strptime(wfh_request.wfh_date, "%Y-%m-%d")
#                 + timedelta(days=i * wfh_request.recurring_frequency_number * 7)
#             ).strftime("%Y-%m-%d")

#         arrangement_copy.batch_id = batch_id

#         # Auto Approve Jack Sim's requests
#         if arrangement_copy.staff_id == 130002:
#             arrangement_copy.current_approval_status = "approved"

#         arrangements_list.append(arrangement_copy)

#     return arrangements_list


# def update_arrangement_approval_status(
#     db: Session, wfh_update: ArrangementUpdate
# ) -> ArrangementUpdate:

#     # TODO: Check that the approving officer is the manager of the employee

#     wfh_update.reason_description = (
#         "[DEFAULT] Approved by Manager"
#         if wfh_update.reason_description is None
#         else wfh_update.reason_description
#     )

#     arrangement: models.LatestArrangement = crud.get_arrangement_by_id(
#         db, wfh_update.arrangement_id
#     )

#     if not arrangement:
#         raise exceptions.ArrangementNotFoundError(wfh_update.arrangement_id)

#     # TODO: Add logic for raising ArrangementActionNotAllowed exceptions based on the current status

#     arrangement.current_approval_status = STATUS.get(wfh_update.action)
#     arrangement.approving_officer = wfh_update.approving_officer
#     arrangement.reason_description = wfh_update.reason_description

#     arrangement: models.LatestArrangement = crud.update_arrangement_approval_status(
#         db, arrangement, wfh_update.action
#     )

#     arrangement_schema = ArrangementUpdate(**arrangement.__dict__, action=wfh_update.action)

#     return arrangement_schema


def update_arrangement_approval_status(
    db: Session, wfh_update: ArrangementUpdate
) -> ArrangementUpdate:
    # TODO: Check that the approving officer is the manager of the employee

    # Set default reason description if not provided
    if wfh_update.reason_description is None:
        wfh_update.reason_description = "[DEFAULT] Approved by Manager"

    # Fetch the arrangement
    arrangement: models.LatestArrangement = crud.get_arrangement_by_id(
        db, wfh_update.arrangement_id
    )

    if not arrangement:
        raise exceptions.ArrangementNotFoundError(wfh_update.arrangement_id)

    # TODO: Add logic for raising ArrangementActionNotAllowed exceptions based on the current status
    # For example:
    # if arrangement.current_approval_status == "approved" and wfh_update.action != "cancel":
    #     raise exceptions.ArrangementActionNotAllowed(f"Cannot {wfh_update.action} an already approved arrangement")

    # Update arrangement fields
    new_status = STATUS.get(wfh_update.action)
    if new_status is None:
        raise ValueError(f"Invalid action: {wfh_update.action}")

    arrangement.current_approval_status = new_status
    arrangement.approving_officer = wfh_update.approving_officer
    arrangement.reason_description = wfh_update.reason_description
    # Update the arrangement in the database

    updated_arrangement: models.LatestArrangement = crud.update_arrangement_approval_status(
        db, arrangement, wfh_update.action

    # Create and return the ArrangementUpdate schema
    arrangement_schema = ArrangementUpdate(
        arrangement_id=updated_arrangement.arrangement_id,
        action=wfh_update.action,
        approving_officer=updated_arrangement.approving_officer,
        reason_description=updated_arrangement.reason_description,
        current_approval_status=updated_arrangement.current_approval_status,

    )
    logger.info(
        f"Arrangement {arrangement.arrangement_id} updated successfully. Status: {arrangement.current_approval_status}"


    return arrangement_schema
