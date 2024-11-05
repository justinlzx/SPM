import inspect
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from fastapi import File
from src.employees.models import Employee

from .enums import Action, ApprovalStatus, RecurringFrequencyUnit, WfhType


@dataclass
class BaseClass:
    """Base class for dataclasses."""

    @classmethod
    def from_dict(cls, env):
        cls_signature = inspect.signature(cls)
        cls_parameters = cls_signature.parameters
        cls_type_hints = {k: v.annotation for k, v in cls_parameters.items()}

        parsed_env = {}
        for k, v in env.items():
            if k in cls_type_hints:
                if cls_type_hints[k] == datetime and isinstance(v, str):
                    try:
                        parsed_env[k] = datetime.fromisoformat(v)
                    except ValueError:
                        parsed_env[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                elif cls_type_hints[k] == date and isinstance(v, str):
                    try:
                        parsed_env[k] = date.fromisoformat(v)
                    except ValueError:
                        parsed_env[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S").date()
                else:
                    parsed_env[k] = v

        return cls(**parsed_env)


@dataclass
class ArrangementFilters(BaseClass):
    """Dataclass for arrangement filters."""

    current_approval_status: Optional[List[ApprovalStatus]] = None
    name: Optional[str] = None
    wfh_type: Optional[List[WfhType]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    group_by_date: Optional[bool] = True
    department: Optional[str] = None


@dataclass
class PaginationConfig(BaseClass):
    """Dataclass for pagination config."""

    items_per_page: int = 10
    page_num: int = 1


@dataclass
class CreateArrangementRequest(BaseClass):
    """Dataclass for arrangement."""

    update_datetime: datetime
    requester_staff_id: int
    wfh_date: date
    wfh_type: WfhType
    is_recurring: bool
    recurring_frequency_number: Optional[int]
    recurring_frequency_unit: Optional[RecurringFrequencyUnit]
    recurring_occurrences: Optional[int]
    # supporting_docs: Optional[List[File]]
    current_approval_status: ApprovalStatus
    approving_officer: Optional[int] = None
    delegate_approving_officer: Optional[int] = None
    reason_description: Optional[str] = None
    batch_id: Optional[int] = None
    supporting_doc_1: Optional[File] = None
    supporting_doc_2: Optional[File] = None
    supporting_doc_3: Optional[File] = None


@dataclass
class UpdateArrangementRequest(BaseClass):
    """Dataclass for arrangement."""

    arrangement_id: int
    update_datetime: datetime
    action: Action
    approving_officer: int
    status_reason: Optional[str] = None
    supporting_doc_1: Optional[File] = None
    supporting_doc_2: Optional[File] = None
    supporting_doc_3: Optional[File] = None
    auto_reject: Optional[bool] = False


@dataclass
class ArrangementResponse(BaseClass):
    """Dataclass for created arrangement."""

    arrangement_id: int
    update_datetime: datetime
    requester_staff_id: int
    wfh_date: date
    wfh_type: WfhType
    current_approval_status: ApprovalStatus
    approving_officer: int
    latest_log_id: Optional[int] = None
    delegate_approving_officer: Optional[int] = None
    reason_description: Optional[str] = None
    batch_id: Optional[int] = None
    supporting_doc_1: Optional[File] = None
    supporting_doc_2: Optional[File] = None
    supporting_doc_3: Optional[File] = None
    status_reason: Optional[str] = None
    requester_info: Optional[Employee] = None


@dataclass
class ArrangementLogResponse(BaseClass):
    """Dataclass for created arrangement."""

    log_id: int
    arrangement_id: int
    update_datetime: datetime
    requester_staff_id: int
    wfh_date: date
    wfh_type: WfhType
    action: Action
    previous_approval_status: ApprovalStatus
    updated_approval_status: ApprovalStatus
    approving_officer: int
    reason_description: Optional[str]
    batch_id: Optional[int]
    supporting_doc_1: Optional[File]
    supporting_doc_2: Optional[File]
    supporting_doc_3: Optional[File]


@dataclass
class CreatedArrangementGroupByDate(BaseClass):
    """Dataclass for created arrangement."""

    date: date
    arrangements: List[ArrangementResponse]


@dataclass
class PaginationMeta(BaseClass):
    """Dataclass for pagination meta."""

    total_count: int
    page_size: int
    page_num: int
    total_pages: int


@dataclass
class RecurringRequestDetails(BaseClass):
    """Dataclass for recurring request details."""

    requester_staff_id: int
    reason_description: Optional[str]
    start_date: date
    recurring_frequency_number: int
    recurring_frequency_unit: RecurringFrequencyUnit
    recurring_occurrences: int
    request_datetime: datetime


@dataclass
class CreatedRecurringRequest(RecurringRequestDetails):
    """Dataclass for created recurring request."""

    batch_id: int
