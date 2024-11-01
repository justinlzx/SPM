from datetime import date, datetime
from typing import Annotated, List, Optional

from fastapi import Form
from pydantic import Field, field_serializer

from ...base import BaseSchema
from .enums import Action, ApprovalStatus, RecurringFrequencyUnit, WfhType


class ArrangementFilters(BaseSchema):
    current_approval_status: Optional[List[ApprovalStatus]] = Field(
        None,
        title="Filter by the current approval status",
    )
    name: Optional[str] = Field(
        None,
        title="Filter by the name of the employee",
    )
    start_date: Optional[date] = Field(
        None,
        title="Filter by the start date of the arrangement",
    )
    end_date: Optional[date] = Field(
        None,
        title="Filter by the end date of the arrangement",
    )
    wfh_type: Optional[List[WfhType]] = Field(
        None,
        title="Filter by the type of the arrangement",
    )
    reason: Optional[str] = Field(
        None,
        title="Filter by the reason for the arrangement",
    )
    group_by_date: Optional[bool] = Field(
        True,
        title="Group by date",
    )


class PaginationConfig(BaseSchema):
    items_per_page: Optional[int] = Field(
        default=10,
        title="Number of items per page",
    )
    page_num: Optional[int] = Field(
        default=1,
        title="Page number",
    )


class PersonalArrangementsRequest(BaseSchema):
    current_approval_status: Optional[List[ApprovalStatus]] = Field(
        None,
        title="Filter by the current approval status",
    )


class CreateArrangementRequest(BaseSchema):
    requester_staff_id: int = Field(
        ...,
        title="Staff ID of the employee who made the request",
        alias="requester_staff_id",
    )
    wfh_date: date = Field(
        ...,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )
    wfh_type: WfhType = Field(
        ...,
        title="Type of WFH arrangement",
    )
    is_recurring: bool = Field(
        False,
        title="Flag to indicate if the request is recurring",
    )
    reason_description: Optional[str] = Field(
        None,
        title="Reason for requesting the WFH",
    )
    recurring_frequency_number: Optional[int] = Field(
        None,
        title="Numerical frequency of the recurring WFH request",
    )
    recurring_frequency_unit: Optional[RecurringFrequencyUnit] = Field(
        None,
        title="Unit of the frequency of the recurring WFH request",
    )
    recurring_occurrences: Optional[int] = Field(
        None,
        title="Number of occurrences of the recurring WFH request",
    )

    @classmethod
    def as_form(
        cls,
        requester_staff_id: Annotated[int, Form()],
        wfh_date: Annotated[date, Form()],
        wfh_type: Annotated[WfhType, Form()],
        is_recurring: Annotated[bool, Form()] = False,
        reason_description: Annotated[Optional[str], Form()] = None,
        recurring_frequency_number: Annotated[Optional[int], Form()] = None,
        recurring_frequency_unit: Annotated[Optional[RecurringFrequencyUnit], Form()] = None,
        recurring_occurrences: Annotated[Optional[int], Form()] = None,
    ):
        return cls(
            requester_staff_id=requester_staff_id,
            wfh_date=wfh_date,
            wfh_type=wfh_type,
            is_recurring=is_recurring,
            reason_description=reason_description,
            recurring_frequency_number=recurring_frequency_number,
            recurring_frequency_unit=recurring_frequency_unit,
            recurring_occurrences=recurring_occurrences,
        )


class UpdateArrangementRequest(BaseSchema):
    action: Action = Field(
        ...,
        title="Action to be performed on the arrangement",
    )
    approving_officer: int = Field(
        ...,
        title="Staff ID of the approving officer",
    )
    status_reason: Optional[str] = Field(
        None,
        title="Reason for the status change",
    )

    @classmethod
    def as_form(
        cls,
        action: Annotated[Action, Form()],
        approving_officer: Annotated[int, Form()],
        status_reason: Annotated[Optional[str], Form()] = None,
    ):
        return cls(
            action=action,
            approving_officer=approving_officer,
            status_reason=status_reason,
        )


class ArrangementResponse(BaseSchema):
    @field_serializer("wfh_date")
    def serialize_wfh_date(self, wfh_date: date) -> str:
        return wfh_date.isoformat()

    @field_serializer("update_datetime")
    def serialize_update_datetime(self, update_datetime: datetime) -> str:
        return update_datetime.isoformat()

    arrangement_id: int = Field(
        ...,
        title="ID of the arrangement",
    )
    update_datetime: datetime = Field(
        ...,
        title="Datetime that the arrangement was last updated",
    )
    requester_staff_id: int = Field(
        ...,
        title="Staff ID of the employee who made the request",
        alias="requester_staff_id",
    )
    wfh_date: date = Field(
        ...,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )
    wfh_type: WfhType = Field(
        ...,
        title="Type of WFH arrangement",
    )
    current_approval_status: ApprovalStatus = Field(
        ...,
        title="Current status of the request",
    )
    approving_officer: int = Field(
        ...,
        title="Staff ID of the approving officer",
    )
    delegate_approving_officer: Optional[int] = Field(
        ...,
        title="Staff ID of the delegate officer",
    )
    reason_description: Optional[str] = Field(
        ...,
        title="Reason for requesting the WFH",
    )
    batch_id: Optional[int] = Field(
        ...,
        title="ID of the batch",
    )
    latest_log_id: int = Field(
        ...,
        title="ID of the latest log",
    )
    supporting_doc_1: Optional[str] = Field(
        ...,
        title="URL of the first supporting document",
    )
    supporting_doc_2: Optional[str] = Field(
        ...,
        title="URL of the second supporting document",
    )
    supporting_doc_3: Optional[str] = Field(
        ...,
        title="URL of the third supporting document",
    )
    status_reason: Optional[str] = Field(
        None,
        title="Reason for the status",
    )


class ArrangementLogResponse(BaseSchema):
    @field_serializer("wfh_date")
    def serialize_wfh_date(self, wfh_date: date) -> str:
        return wfh_date.isoformat()

    @field_serializer("update_datetime")
    def serialize_update_datetime(self, update_datetime: datetime) -> str:
        return update_datetime.isoformat()

    log_id: int = Field(
        ...,
        title="ID of the log",
    )
    update_datetime: datetime = Field(
        ...,
        title="Datetime that the log was last updated",
    )
    requester_staff_id: int = Field(
        ...,
        title="Staff ID of the employee who made the request",
        alias="requester_staff_id",
    )
    wfh_date: date = Field(
        ...,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )
    wfh_type: WfhType = Field(
        ...,
        title="Type of WFH arrangement",
    )
    action: Action = Field(
        ...,
        title="Action taken on the arrangement",
    )
    previous_approval_status: Optional[ApprovalStatus] = Field(
        None,
        title="Previous status of the request",
    )
    updated_approval_status: ApprovalStatus = Field(
        ...,
        title="Updated status of the request",
    )
    approving_officer: int = Field(
        ...,
        title="Staff ID of the approving officer",
    )
    reason_description: Optional[str] = Field(
        ...,
        title="Reason for requesting the WFH",
    )
    batch_id: Optional[int] = Field(
        ...,
        title="ID of the batch",
    )
    supporting_doc_1: Optional[str] = Field(
        ...,
        title="URL of the first supporting document",
    )
    supporting_doc_2: Optional[str] = Field(
        ...,
        title="URL of the second supporting document",
    )
    supporting_doc_3: Optional[str] = Field(
        ...,
        title="URL of the third supporting document",
    )
    status_reason: Optional[str] = Field(
        None,
        title="Reason for the status",
    )
