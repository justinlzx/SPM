from dataclasses import asdict, replace
from datetime import datetime
from math import ceil
from typing import List, Optional, Tuple, Union

import boto3
import botocore
import botocore.exceptions
from dateutil.relativedelta import relativedelta
from fastapi import File
from sqlalchemy.orm import Session
from src.arrangements.utils import delete_file, upload_file

from ..arrangements.utils import delete_file, upload_file
from ..employees import crud as employee_crud
from ..employees import models as employee_models
from ..employees import services as employee_services
from ..logger import logger
from ..notifications.email_notifications import craft_and_send_email
from . import crud
from .commons import exceptions
from .commons.dataclasses import (
    ArrangementFilters,
    ArrangementResponse,
    CreateArrangementRequest,
    CreatedArrangementGroupByDate,
    PaginationConfig,
    PaginationMeta,
    RecurringRequestDetails,
    UpdateArrangementRequest,
)
from .commons.enums import STATUS_ACTION_MAPPING, Action, ApprovalStatus
from .utils import create_presigned_url


def get_arrangement_by_id(db: Session, arrangement_id: int) -> ArrangementResponse:
    arrangement = crud.get_arrangement_by_id(db, arrangement_id)

    if not arrangement:
        raise exceptions.ArrangementNotFoundException(arrangement_id)

    return ArrangementResponse.from_dict(arrangement)


def get_personal_arrangements(
    db: Session, staff_id: int, current_approval_status: Optional[List[ApprovalStatus]] = None
) -> List[ArrangementResponse]:

    filters = ArrangementFilters(current_approval_status=current_approval_status)

    logger.info(f"Service: Fetching personal arrangements for staff ID {staff_id}")
    arrangements = crud.get_arrangements_by_staff_ids(db, [staff_id], filters=filters)
    logger.info(f"Service: Found {len(arrangements)} arrangements for staff ID {staff_id}")

    return [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]


def get_subordinates_arrangements(
    db: Session,
    manager_id: int,
    filters: ArrangementFilters,
    pagination: PaginationConfig,
) -> Tuple[Union[List[ArrangementResponse], List[CreatedArrangementGroupByDate]], PaginationMeta]:

    # Get subordinates of the manager
    employees_under_manager = employee_services.get_subordinates_by_manager_id(db, manager_id)
    employees_under_manager = [
        employees_under_manager.__dict__ for employees_under_manager in employees_under_manager
    ]
    employees_under_manager_ids = [employee["staff_id"] for employee in employees_under_manager]

    # Get arrangements for the subordinates
    logger.info(f"Service: Fetching arrangements for employees under manager ID: {manager_id}")
    arrangements = crud.get_arrangements_by_staff_ids(
        db=db,
        staff_ids=employees_under_manager_ids,
        filters=filters,
    )
    arrangements = [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]
    logger.info(f"Service: Found {len(arrangements)} arrangements")

    # Get presigned URL for each supporting document in each arrangement
    for record in arrangements:
        record.supporting_doc_1 = create_presigned_url(record.supporting_doc_1)
        record.supporting_doc_2 = create_presigned_url(record.supporting_doc_2)
        record.supporting_doc_3 = create_presigned_url(record.supporting_doc_3)

    total_count = len(arrangements)
    total_pages = ceil(total_count / pagination.items_per_page)

    # Group by date if required
    if filters.group_by_date:
        arrangements = group_arrangements_by_date(arrangements)

        logger.info(f"Grouped arrangements into {len(arrangements)} dates")

        # Pagination logic
        total_count = len(arrangements)

        # slice the list based on page number and items per page
        arrangements = arrangements[
            (pagination.page_num - 1)
            * pagination.items_per_page : pagination.page_num
            * pagination.items_per_page
        ]

    pagination_meta = PaginationMeta(
        total_count=total_count,
        page_size=pagination.items_per_page,
        page_num=pagination.page_num,
        total_pages=total_pages,
    )

    return arrangements, pagination_meta


def group_arrangements_by_date(
    arrangements: List[ArrangementResponse],
) -> List[CreatedArrangementGroupByDate]:
    arrangements_dict = {}

    logger.info(f"Grouping {len(arrangements)} arrangements by date")
    for arrangement in arrangements:
        arrangements_dict.setdefault(arrangement.wfh_date.isoformat(), []).append(arrangement)

    result = []
    for key, val in arrangements_dict.items():
        result.append(CreatedArrangementGroupByDate(date=key, arrangements=val))
    logger.info(f"Service: Grouped into {len(result)} dates")
    return result


def get_team_arrangements(
    db: Session,
    staff_id: int,
    filters: ArrangementFilters,
    pagination: PaginationConfig,
) -> Tuple[Union[List[ArrangementResponse], List[CreatedArrangementGroupByDate]], PaginationMeta]:

    # Get peer employees
    employees: List[employee_models.Employee] = []
    employees.extend(employee_services.get_peers_by_staff_id(db, staff_id))

    # Get subordinate employees
    employees.extend(employee_services.get_subordinates_by_manager_id(db, staff_id))

    # Get team arrangements
    logger.info(f"Service: Fetching arrangements for team of staff ID {staff_id}")
    arrangements = crud.get_arrangements_by_staff_ids(
        db=db,
        staff_ids=[employee.staff_id for employee in employees],
        filters=filters,
    )
    arrangements = [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]
    logger.info(f"Service: Found {len(arrangements)} arrangements")

    total_count = len(arrangements)
    total_pages = ceil(total_count / pagination.items_per_page)

    # Group by date if required
    if filters.group_by_date:
        arrangements = group_arrangements_by_date(arrangements)

        logger.info(f"Grouped arrangements into {len(arrangements)} dates")

        # Pagination logic
        total_count = len(arrangements)

        # slice the list based on page number and items per page
        arrangements = arrangements[
            (pagination.page_num - 1)
            * pagination.items_per_page : pagination.page_num
            * pagination.items_per_page
        ]

    pagination_meta = PaginationMeta(
        total_count=total_count,
        page_size=pagination.items_per_page,
        page_num=pagination.page_num,
        total_pages=total_pages,
    )

    return arrangements, pagination_meta


async def create_arrangements_from_request(
    db: Session,
    wfh_request: CreateArrangementRequest,
    supporting_docs: List[File],
) -> List[ArrangementResponse]:
    try:
        # Get all required staff objects
        employee = employee_crud.get_employee_by_staff_id(db, wfh_request.requester_staff_id)
        approving_officer, _ = employee_services.get_manager_by_subordinate_id(
            db=db, staff_id=wfh_request.requester_staff_id
        )
        delegation = employee_crud.get_existing_delegation(
            db=db, staff_id=approving_officer.staff_id, delegate_manager_id=None
        )

        # Assign approving officers
        wfh_request.approving_officer = approving_officer.__dict__["staff_id"]
        if delegation:
            wfh_request.delegate_approving_officer = delegation.__dict__["delegate_manager_id"]

        # Auto Approve Jack Sim's requests
        if wfh_request.requester_staff_id == 130002:
            wfh_request.current_approval_status = ApprovalStatus.APPROVED

        # Upload supporting documents to S3 bucket
        s3_client = boto3.client("s3")
        file_paths = []
        created_arrangements = []

        for file in supporting_docs:
            if file:
                response = await upload_file(
                    wfh_request.requester_staff_id,
                    wfh_request.update_datetime.isoformat(),
                    file,
                    s3_client,
                )

                file_paths.append(response["file_url"])

        # Update request with the file paths to the documents in S3
        wfh_request.supporting_doc_1 = file_paths[0] if file_paths else None
        wfh_request.supporting_doc_2 = file_paths[1] if len(file_paths) > 1 else None
        wfh_request.supporting_doc_3 = file_paths[2] if len(file_paths) > 2 else None

        # Create and expand recurring arrangements
        arrangements = []

        if wfh_request.is_recurring:
            batch = crud.create_recurring_request(
                db=db,
                request=RecurringRequestDetails.from_dict(
                    {
                        "request_datetime": wfh_request.update_datetime,
                        "start_date": wfh_request.wfh_date,
                        **asdict(wfh_request),
                    }
                ),
            )

            wfh_request.batch_id = batch.batch_id

            arrangements = expand_recurring_arrangement(request=wfh_request)
        else:
            arrangements.append(wfh_request)

        # Create arrangements in the database
        logger.info(f"Service: Creating {len(arrangements)} arrangements")
        created_arrangements = crud.create_arrangements(db=db, arrangements=arrangements)
        logger.info(f"Service: Created {len(created_arrangements)} arrangements")

        # Send notification emails
        await craft_and_send_email(
            employee=employee,
            arrangements=created_arrangements,
            action=Action.CREATE,
            current_approval_status=wfh_request.current_approval_status,
            manager=approving_officer,
        )

        return created_arrangements

    except botocore.exceptions.ClientError as upload_error:
        # If any error occurs, delete uploaded files from S3
        logger.info(f"Deleting files due to error: {str(upload_error)}")
        if file_paths:
            for path in file_paths:
                try:
                    await delete_file(path, datetime.now(), s3_client)
                except botocore.exceptions.ClientError as delete_error:
                    # Log deletion error, but do not raise to avoid overriding the main exception
                    logger.info(f"Error deleting file {path} from S3: {str(delete_error)}")
        raise exceptions.S3UploadFailedException(str(upload_error))
    # TODO: Email notification error


from datetime import datetime, timedelta, date
from typing import List
from dateutil.relativedelta import relativedelta


def expand_recurring_arrangement(
    request: CreateArrangementRequest,
) -> List[CreateArrangementRequest]:
    arrangements_list = []

    for i in range(request.recurring_occurrences):
        arrangement_copy = replace(request)

        if request.recurring_frequency_unit.value == "week":
            arrangement_copy.wfh_date = request.wfh_date + relativedelta(
                weeks=i * request.recurring_frequency_number
            )
        else:
            arrangement_copy.wfh_date = request.wfh_date + relativedelta(
                months=i * request.recurring_frequency_number
            )

        arrangements_list.append(arrangement_copy)

    return arrangements_list


async def update_arrangement_approval_status(
    db: Session, wfh_update: UpdateArrangementRequest, supporting_docs: List[File]
) -> ArrangementResponse:
    # TODO: Check that the approving officer is the manager of the employee

    # Get the arrangement to be updated
    arrangement = crud.get_arrangement_by_id(db, wfh_update.arrangement_id)

    if not arrangement:
        raise exceptions.ArrangementNotFoundException(wfh_update.arrangement_id)

    arrangement = ArrangementResponse.from_dict(arrangement)

    # Update arrangement fields

    if wfh_update.action not in STATUS_ACTION_MAPPING[arrangement.current_approval_status]:
        raise exceptions.ArrangementActionNotAllowedException(
            arrangement.current_approval_status, wfh_update.action
        )

    previous_approval_status = arrangement.current_approval_status
    arrangement.current_approval_status = STATUS_ACTION_MAPPING[
        arrangement.current_approval_status
    ][wfh_update.action]

    arrangement.approving_officer = wfh_update.approving_officer
    arrangement.status_reason = wfh_update.status_reason

    # Update arrangement in database
    logger.info(f"Service: Updating arrangement {wfh_update.arrangement_id}")
    updated_arrangement = crud.update_arrangement_approval_status(
        db=db,
        arrangement_data=arrangement,
        action=wfh_update.action,
        previous_approval_status=previous_approval_status,
    )
    updated_arrangement = ArrangementResponse.from_dict(updated_arrangement)
    logger.info(
        f"Service: Updated '{wfh_update.action.value}' arrangement to '{updated_arrangement.current_approval_status.value}' status"
    )

    # Get required staff objects
    employee = employee_crud.get_employee_by_staff_id(db, updated_arrangement.requester_staff_id)
    approving_officer = employee_crud.get_employee_by_staff_id(db, wfh_update.approving_officer)

    # Send email notifications
    await craft_and_send_email(
        employee=employee,
        arrangements=[updated_arrangement],
        action=wfh_update.action,
        current_approval_status=updated_arrangement.current_approval_status,
        manager=approving_officer,
    )

    return updated_arrangement


# ============================ DEPRECATED FUNCTIONS ============================
# def group_arrangements_by_employee(
#     arrangements_schema: List[ArrangementCreateResponse],
# ) -> List[ManagerPendingRequests]:
#     """
#     The function `group_arrangements_by_employee` organizes a list of arrangements by employee, creating
#     a list of ManagerPendingRequests objects for each employee with their corresponding arrangements.

#     :param arrangements_schema: `arrangements_schema` is a list of `ArrangementCreateResponse` objects
#     :type arrangements_schema: List[ArrangementCreateResponse]
#     :return: A list of `ManagerPendingRequests` objects, where each object contains information about an
#     employee and their pending arrangements.
#     """

#     arrangements_dict = {}

#     for arrangement in arrangements_schema:
#         staff_id = arrangement.staff_id
#         if staff_id not in arrangements_dict:
#             arrangements_dict[staff_id] = []

#         arrangements_dict[staff_id].append(arrangement)

#     result = []
#     for _, val in arrangements_dict.items():
#         result.append(
#             ManagerPendingRequests(employee=val[0].requester_info, pending_arrangements=val)
#         )

#     return result

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

# def get_approving_officer(arrangement: LatestArrangement):
#     """Returns the delegate approving officer if present, otherwise the original approving
#     officer."""
#     if arrangement.delegate_approving_officer:
#         return arrangement.delegate_approving_officer_info
#     return arrangement.approving_officer_info
