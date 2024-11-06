from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import boto3
import botocore
import botocore.exceptions
from fastapi import File
from sqlalchemy.orm import Session

from ..database import get_db
from ..employees import crud as employee_crud
from ..employees import services as employee_services
from ..employees.exceptions import EmployeeNotFoundException
from ..logger import logger
from ..notifications.commons.dataclasses import ArrangementNotificationConfig
from ..notifications.email_notifications import craft_and_send_email
from . import crud
from .commons import exceptions
from .commons.dataclasses import (
    ArrangementFilters,
    ArrangementLogResponse,
    ArrangementResponse,
    CreateArrangementRequest,
    CreatedArrangementGroupByDate,
    PaginationConfig,
    PaginationMeta,
    RecurringRequestDetails,
    UpdateArrangementRequest,
)
from .commons.enums import STATUS_ACTION_MAPPING, Action, ApprovalStatus
from .utils import (
    compute_pagination_meta,
    create_presigned_url,
    expand_recurring_arrangement,
    group_arrangements_by_date,
    handle_multi_file_deletion,
    upload_file,
)


def get_arrangement_by_id(db: Session, arrangement_id: int) -> ArrangementResponse:
    arrangement = crud.get_arrangement_by_id(db, arrangement_id)

    if not arrangement:
        raise exceptions.ArrangementNotFoundException(arrangement_id)

    return ArrangementResponse.from_dict(arrangement)


def get_all_arrangements(db: Session, filters: ArrangementFilters) -> List[ArrangementResponse]:
    arrangements: List[Dict] = crud.get_arrangements(db, filters=filters)

    response = [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]

    return response


def get_personal_arrangements(
    db: Session, staff_id: int, current_approval_status: Optional[List[ApprovalStatus]] = None
) -> List[ArrangementResponse]:
    filters = ArrangementFilters(
        current_approval_status=current_approval_status, staff_ids=staff_id
    )

    logger.info(f"Service: Fetching personal arrangements for staff ID {staff_id}")
    arrangements = crud.get_arrangements(db, filters=filters)
    logger.info(f"Service: Found {len(arrangements)} arrangements for staff ID {staff_id}")

    arrangements = [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]

    if len(arrangements) > 0:
        # Get presigned URL for each supporting document in each arrangement
        for record in arrangements:
            record.supporting_doc_1 = create_presigned_url(record.supporting_doc_1)
            record.supporting_doc_2 = create_presigned_url(record.supporting_doc_2)
            record.supporting_doc_3 = create_presigned_url(record.supporting_doc_3)

    logger.info(f"Service: Found {len(arrangements)} arrangements")

    return arrangements


def get_subordinates_arrangements(
    db: Session,
    manager_id: int,
    filters: ArrangementFilters,
    pagination: PaginationConfig,
) -> Tuple[Union[List[ArrangementResponse], List[CreatedArrangementGroupByDate]], PaginationMeta]:

    # Get arrangements for the subordinates
    logger.info(f"Service: Fetching arrangements for employees under manager ID: {manager_id}")
    filters.manager_id = manager_id
    arrangements = crud.get_arrangements(
        db=db,
        filters=filters,
    )
    arrangements = [ArrangementResponse.from_dict(arrangement) for arrangement in arrangements]
    logger.info(f"Service: Found {len(arrangements)} arrangements")

    # Get presigned URL for each supporting document in each arrangement
    for record in arrangements:
        record.supporting_doc_1 = create_presigned_url(record.supporting_doc_1)
        record.supporting_doc_2 = create_presigned_url(record.supporting_doc_2)
        record.supporting_doc_3 = create_presigned_url(record.supporting_doc_3)

    # Group by date if required
    if filters.group_by_date:
        arrangements = group_arrangements_by_date(arrangements)

        logger.info(f"Grouped arrangements into {len(arrangements)} dates")

        # slice the list based on page number and items per page
        arrangements = arrangements[
            (pagination.page_num - 1)
            * pagination.items_per_page : pagination.page_num
            * pagination.items_per_page
        ]

    pagination_meta = compute_pagination_meta(
        arrangements, pagination.items_per_page, pagination.page_num
    )

    return arrangements, pagination_meta


def get_team_arrangements(
    db: Session,
    staff_id: int,
    filters: ArrangementFilters,
    pagination: PaginationConfig,
) -> Tuple[Union[List[ArrangementResponse], List[CreatedArrangementGroupByDate]], PaginationMeta]:

    # Get peer employees
    employees = employee_services.get_peers_by_staff_id(db, staff_id)

    team_arrangements = []

    # Get peer arrangements
    filters.staff_ids = [employee.staff_id for employee in employees]  # type: ignore
    logger.info(f"Service: Fetching arrangements for peers of staff ID {staff_id}")
    peer_arrangements = crud.get_arrangements(
        db=db,
        filters=filters,
    )
    team_arrangements.extend(peer_arrangements)
    logger.info(f"Service: Found {len(peer_arrangements)} peer arrangements")

    # Get subordinate arrangements
    filters.staff_ids = None
    filters.manager_id = staff_id
    logger.info(f"Service: Fetching arrangements for team of staff ID {staff_id}")
    subordinates_arrangements = crud.get_arrangements(
        db=db,
        filters=filters,
    )
    team_arrangements.extend(subordinates_arrangements)
    logger.info(f"Service: Found {len(subordinates_arrangements)} subordinates arrangements")

    # Convert to dataclasses
    team_arrangements = [
        ArrangementResponse.from_dict(arrangement) for arrangement in team_arrangements
    ]

    # Get presigned URL for each supporting document in each arrangement
    for record in team_arrangements:
        record.supporting_doc_1 = create_presigned_url(record.supporting_doc_1)
        record.supporting_doc_2 = create_presigned_url(record.supporting_doc_2)
        record.supporting_doc_3 = create_presigned_url(record.supporting_doc_3)

    # Group by date if required
    if filters.group_by_date:
        team_arrangements = group_arrangements_by_date(team_arrangements)

        logger.info(f"Grouped arrangements into {len(team_arrangements)} dates")

        # slice the list based on page number and items per page
        team_arrangements = team_arrangements[
            (pagination.page_num - 1)
            * pagination.items_per_page : pagination.page_num
            * pagination.items_per_page
        ]

    pagination_meta = compute_pagination_meta(
        team_arrangements, pagination.items_per_page, pagination.page_num
    )

    return team_arrangements, pagination_meta


def get_arrangement_logs(
    db: Session,
) -> List[ArrangementLogResponse]:
    arrangement_logs = crud.get_arrangement_logs(db)
    arrangement_logs = [
        ArrangementLogResponse.from_dict(arrangement) for arrangement in arrangement_logs
    ]

    return arrangement_logs


async def create_arrangements_from_request(
    db: Session,
    wfh_request: CreateArrangementRequest,
    supporting_docs: List[File],
) -> List[ArrangementResponse]:
    try:
        # Get all required staff objects
        employee = employee_crud.get_employee_by_staff_id(db, wfh_request.requester_staff_id)

        if employee is None:
            raise EmployeeNotFoundException(wfh_request.requester_staff_id)

        approving_officer, _ = employee_services.get_manager_by_subordinate_id(
            db=db, staff_id=wfh_request.requester_staff_id
        )
        delegation = None

        # Assign approving officers
        if approving_officer:
            wfh_request.approving_officer = approving_officer.__dict__["staff_id"]
            delegation = employee_crud.get_existing_delegation(
                db=db, staff_id=approving_officer.staff_id, delegate_manager_id=None
            )
        if delegation:
            wfh_request.delegate_approving_officer = delegation.__dict__["delegate_manager_id"]

        # Auto Approve Jack Sim's requests
        if wfh_request.requester_staff_id == 130002:
            wfh_request.current_approval_status = ApprovalStatus.APPROVED

        # Upload supporting documents to S3 bucket
        s3_client = boto3.client("s3")
        file_paths = []
        created_arrangements = []

        logger.info(f"Service: Uploading {len(supporting_docs)} supporting documents to S3")
        for file in supporting_docs:
            response = await upload_file(
                wfh_request.requester_staff_id,
                wfh_request.update_datetime.isoformat(),
                file,
                s3_client,
            )

            file_paths.append(response["file_url"])
        logger.info(f"Service: Successfully uploaded {len(file_paths)} supporting documents to S3")

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

        # Create config object for email notifications
        notification_config = ArrangementNotificationConfig(
            employee=employee,
            arrangements=created_arrangements,
            action=Action.CREATE,
            current_approval_status=wfh_request.current_approval_status,
            manager=approving_officer,
        )

        # Send notification emails
        await craft_and_send_email(notification_config)

        return created_arrangements

    except botocore.exceptions.ClientError as upload_error:
        # If any error occurs, delete uploaded files from S3
        logger.info(f"Deleting files due to error: {str(upload_error)}")
        await handle_multi_file_deletion(file_paths, s3_client)
        raise exceptions.S3UploadFailedException(str(upload_error))


async def update_arrangement_approval_status(
    db: Session, wfh_update: UpdateArrangementRequest, supporting_docs: List[File]
) -> ArrangementResponse:
    # TODO: Check that the approving officer is the manager of the employee

    # Get the arrangement to be updated
    arrangement = crud.get_arrangement_by_id(db, wfh_update.arrangement_id)
    if not arrangement:
        raise exceptions.ArrangementNotFoundException(wfh_update.arrangement_id)
    arrangement = ArrangementResponse.from_dict(arrangement)

    # Check if action is valid for the current status
    if wfh_update.action not in STATUS_ACTION_MAPPING[arrangement.current_approval_status]:
        raise exceptions.ArrangementActionNotAllowedException(
            arrangement.current_approval_status, wfh_update.action
        )

    # Update arrangement fields
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

    # Create config object for email notifications
    notification_config = ArrangementNotificationConfig(
        employee=employee,
        arrangements=[updated_arrangement],
        action=wfh_update.action,
        current_approval_status=updated_arrangement.current_approval_status,
        manager=approving_officer,
        auto_reject=wfh_update.auto_reject,
    )

    # Send email notifications
    await craft_and_send_email(notification_config)

    return updated_arrangement


async def auto_reject_old_requests():
    db = next(get_db())
    wfh_requests = crud.get_expiring_requests(db)
    total_count = len(wfh_requests)
    failure_ids = []

    for arrangement in wfh_requests:
        if (
            "delegate_approving_officer" in arrangement
            and arrangement["delegate_approving_officer"]
        ):
            approving_officer = arrangement["delegate_approving_officer"]
        else:
            approving_officer = arrangement["approving_officer"]

        wfh_update = UpdateArrangementRequest(
            arrangement_id=arrangement["arrangement_id"],
            update_datetime=datetime.now(),
            action=Action.REJECT,
            approving_officer=approving_officer,
            status_reason="AUTO-REJECTED due to pending status one day before WFH date",
            auto_reject=True,
        )

        try:
            await update_arrangement_approval_status(
                db=db,
                wfh_update=wfh_update,
                supporting_docs=[],
            )

            logger.info(
                f"Auto-rejected arrangement {arrangement['arrangement_id']} for date {arrangement['wfh_date']}"
            )
        except Exception as e:
            logger.error(
                f"Error processing arrangement {arrangement['arrangement_id']}: {str(e)}",
                exc_info=True,
            )
            failure_ids.append(arrangement["arrangement_id"])

    if failure_ids:
        logger.info(f"Auto-rejection for {len(failure_ids)} of {total_count} requests failed")
    else:
        logger.info(f"Auto-rejection for {total_count} requests completed successfully")
    logger.info(f"The following arrangement IDs failed: {failure_ids}")


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
