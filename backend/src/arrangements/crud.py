from dataclasses import asdict
from typing import Dict, List, Optional, Union

# from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, class_mapper
from src.employees.models import (
    Employee,  # Ensure Employee model is correctly defined and imported
)

from ..logger import logger
from .commons import models
from .commons.dataclasses import (
    ArrangementFilters,
    ArrangementResponse,
    CreateArrangementRequest,
    CreatedRecurringRequest,
    RecurringRequestDetails,
)
from .commons.enums import Action, ApprovalStatus


def get_arrangement_by_id(db: Session, arrangement_id: int) -> Optional[Dict]:
    response = db.query(models.LatestArrangement).get(arrangement_id)
    return response.__dict__ if response else None


def get_arrangements(
    db: Session,
    staff_ids: Union[None, int, List[int]] = None,
    filters: Union[None, ArrangementFilters] = None,
) -> List[Dict]:
    query = db.query(models.LatestArrangement)
    query = query.join(Employee, Employee.staff_id == models.LatestArrangement.requester_staff_id)

    if staff_ids:
        staff_ids = list(set(staff_ids)) if isinstance(staff_ids, list) else staff_ids

        # Log the number of staff IDs being fetched
        logger.info(
            f"Crud: Fetching arrangements for {len(staff_ids) if isinstance(staff_ids, list) else 1} staff IDs with filters"
        )

        # TODO
        # Log all non-null filters
        # non_null_filters = {key: value for key, value in filters.items() if value}
        # logger.info(f"Crud: Applying filters: {non_null_filters}")

        if isinstance(staff_ids, int):
            query = query.filter(models.LatestArrangement.requester_staff_id == staff_ids)
        else:
            query = query.filter(models.LatestArrangement.requester_staff_id.in_(staff_ids))

    if filters:
        # Apply optional filters
        if filters.name:
            query = query.filter(
                or_(
                    Employee.staff_fname.ilike(f"%{filters.name}%"),
                    Employee.staff_lname.ilike(f"%{filters.name}%"),
                )
            )
        if filters.current_approval_status:
            query = query.filter(
                models.LatestArrangement.current_approval_status.in_(
                    filters.current_approval_status
                )
            )

        if filters.wfh_type:
            models.LatestArrangement.wfh_type.in_(filters.wfh_type)

        if filters.start_date:
            query = query.filter(func.date(models.LatestArrangement.wfh_date) >= filters.start_date)

        if filters.end_date:
            query = query.filter(func.date(models.LatestArrangement.wfh_date) <= filters.end_date)

        if filters.reason:
            query = query.filter(models.LatestArrangement.reason_description.like(filters.reason))

        if filters.department:
            query = query.filter(Employee.dept == filters.department)

    results = query.all()
    logger.info(f"Crud: Found {len(results)} arrangements")

    return [result.__dict__ for result in results]


def get_team_arrangements(
    db: Session,
    staff_id: int,
    filters: ArrangementFilters,
) -> List[Dict]:
    # Log the team lead's staff ID
    logger.info(f"Crud: Fetching team arrangements for team lead {staff_id}")

    # Fetch the team members' staff IDs
    team_members = db.query(Employee.staff_id).filter(Employee.manager_staff_id == staff_id).all()
    team_member_ids = [member[0] for member in team_members]

    # Fetch the team members' arrangements
    return get_arrangements(db, team_member_ids, filters)


def get_arrangement_logs(
    db: Session,
) -> List[Dict]:
    # TODO: Pagination and filters if have time
    query = db.query(models.ArrangementLog)
    query = query.order_by(models.ArrangementLog.update_datetime.desc())

    logs = query.all()

    return [log.__dict__ for log in logs]


def create_arrangement_log(
    db: Session,
    arrangement: models.LatestArrangement,
    action: Action,
    previous_approval_status: ApprovalStatus,
) -> models.ArrangementLog:
    logger.info(f"Crud: Creating arrangement log for action {action}")

    arrangement_log = models.ArrangementLog(
        arrangement_id=arrangement.arrangement_id,
        update_datetime=arrangement.update_datetime,
        requester_staff_id=arrangement.requester_staff_id,
        wfh_date=arrangement.wfh_date,
        wfh_type=arrangement.wfh_type,
        action=action,
        previous_approval_status=previous_approval_status,
        updated_approval_status=arrangement.current_approval_status,
        approving_officer=arrangement.approving_officer,
        reason_description=arrangement.reason_description,
        supporting_doc_1=arrangement.supporting_doc_1,
        supporting_doc_2=arrangement.supporting_doc_2,
        supporting_doc_3=arrangement.supporting_doc_3,
    )

    db.add(arrangement_log)
    db.flush()
    return arrangement_log


def create_recurring_request(
    db: Session,
    request: RecurringRequestDetails,
) -> CreatedRecurringRequest:
    try:
        request_mapper = class_mapper(models.RecurringRequest)
        recurring_request = models.RecurringRequest(
            **{k: v for k, v in asdict(request).items() if k in request_mapper.attrs.keys()},
        )
        db.add(recurring_request)
        db.commit()
        db.refresh(recurring_request)
        return CreatedRecurringRequest.from_dict(recurring_request.__dict__)
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_arrangements(
    db: Session,
    arrangements: List[CreateArrangementRequest],
) -> List[ArrangementResponse]:
    try:
        created_arrangements = []
        for arrangement_data in arrangements:
            arrangement_mapper = class_mapper(models.LatestArrangement)
            arrangement = models.LatestArrangement(
                **{
                    k: v
                    for k, v in asdict(arrangement_data).items()
                    if k in arrangement_mapper.attrs.keys()
                },
            )
            db.add(arrangement)
            db.flush()
            created_arrangements.append(arrangement)
            created_arrangement_log = create_arrangement_log(
                db, arrangement, Action.CREATE, previous_approval_status=None
            )
            arrangement.latest_log_id = created_arrangement_log.log_id
            db.add(created_arrangement_log)
            db.flush()

        db.commit()

        for created_arrangement in created_arrangements:
            db.refresh(created_arrangement)

        created_arrangements = [
            ArrangementResponse.from_dict(arrangement.__dict__)
            for arrangement in created_arrangements
        ]

        return created_arrangements
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_arrangement_approval_status(
    db: Session,
    arrangement_data: ArrangementResponse,
    action: Action,
    previous_approval_status: ApprovalStatus,
) -> Dict:
    try:
        db.query(models.LatestArrangement).filter(
            models.LatestArrangement.arrangement_id == arrangement_data.arrangement_id
        ).update(
            {
                "current_approval_status": arrangement_data.current_approval_status,
                "supporting_doc_1": arrangement_data.supporting_doc_1,
                "supporting_doc_2": arrangement_data.supporting_doc_2,
                "supporting_doc_3": arrangement_data.supporting_doc_3,
                "status_reason": arrangement_data.status_reason,
            }
        )

        updated_arrangement = db.query(models.LatestArrangement).get(
            arrangement_data.arrangement_id
        )

        if updated_arrangement:
            log = create_arrangement_log(db, updated_arrangement, action, previous_approval_status)
            updated_arrangement.latest_log_id = log.log_id

            db.commit()
            db.refresh(updated_arrangement)

        return updated_arrangement.__dict__
    except SQLAlchemyError as e:
        db.rollback()
        raise e
