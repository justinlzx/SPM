from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from pydantic.json_schema import SkipJsonSchema

from ..base import BaseSchema
from ..employees import schemas as employee_schemas


class ArrangementBase(BaseSchema):
    staff_id: int = Field(
        ...,
        title="Staff ID of the employee who made the request",
        alias="requester_staff_id",
    )

    wfh_date: str = Field(
        ...,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )

    wfh_type: Literal["full", "am", "pm"] = Field(..., title="Type of WFH arrangement")


class ArrangementCreate(ArrangementBase):
    @field_validator("recurring_frequency_number", "recurring_occurrences")
    def validate_recurring_fields(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("is_recurring"):
            if v is None or v == 0:
                field_name = (
                    "recurring_frequency_number"
                    if v == info.data.get("recurring_frequency_number")
                    else "recurring_occurrences"
                )
                raise ValueError(
                    f"When 'is_recurring' is True, '{field_name}' must have a non-zero value"
                )
        return v

    approving_officer: Optional[int] = Field(
        ..., title="Staff ID of the approving officer"
    )
    reason_description: str = Field(..., title="Reason for requesting the WFH")

    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the request was created",
    )
    current_approval_status: SkipJsonSchema[str] = Field(
        default="pending", exclude=True, title="Approval status of the request"
    )
    is_recurring: Optional[bool] = Field(
        default=False, title="Flag to indicate if the request is recurring"
    )
    recurring_end_date: Optional[str] = Field(
        default=None, title="End date of a recurring WFH request"
    )
    recurring_frequency_number: Optional[int] = Field(
        default=None, title="Numerical frequency of the recurring WFH request"
    )
    recurring_frequency_unit: Optional[Literal["week", "month"]] = Field(
        default=None, title="Unit of the frequency of the recurring WFH request"
    )
    recurring_occurrences: Optional[int] = Field(
        default=None, title="Number of occurrences of the recurring WFH request"
    )
    batch_id: Optional[int] = Field(
        default=None, title="Unique identifier for the batch, if any"
    )

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Include excluded fields in the dump
        data["update_datetime"] = self.update_datetime
        data["current_approval_status"] = self.current_approval_status
        return data

    class Config:
        arbitrary_types_allowed = True


class ArrangementCreateWithFile(ArrangementCreate):
    supporting_doc_1: Optional[str] = Field(
        default=None, title="URL of the first supporting document"
    )
    supporting_doc_2: Optional[str] = Field(
        default=None, title="URL of the second supporting document"
    )
    supporting_doc_3: Optional[str] = Field(
        default=None, title="URL of the third supporting document"
    )

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Include excluded fields in the dump
        data["update_datetime"] = self.update_datetime
        data["current_approval_status"] = self.current_approval_status
        return data


class ArrangementCreateResponse(ArrangementCreateWithFile):
    requester_info: Optional[employee_schemas.EmployeeBase]


class ArrangementUpdate(ArrangementBase):
    action: Literal["approve", "reject", "withdraw", "cancel"] = Field(
        exclude=True, title="Action to be taken on the WFH request"
    )
    approving_officer: int = Field(
        exclude=True, title="Staff ID of the approving officer"
    )
    reason_description: Optional[str] = Field(
        None, title="Reason for the status update"
    )
    arrangement_id: SkipJsonSchema[int] = Field(
        None, title="Unique identifier for the arrangement"
    )
    staff_id: SkipJsonSchema[int] = Field(
        None,
        title="Staff ID of the employee who made the request",
        alias="requester_staff_id",
    )
    wfh_date: SkipJsonSchema[str] = Field(
        None,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )
    wfh_type: SkipJsonSchema[Literal["full", "am", "pm"]] = Field(
        None, title="Type of WFH arrangement"
    )
    batch_id: SkipJsonSchema[Optional[int]] = Field(
        None, title="Unique identifier for the batch, if any"
    )  # Allow None
    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the arrangement was updated",
    )
    current_approval_status: SkipJsonSchema[str] = Field(
        None, title="Approval status of the request"
    )


class ArrangementLog(ArrangementBase):
    arrangement_id: int = Field(..., title="Unique identifier for the arrangement")
    update_datetime: datetime = Field(..., title="Datetime of the arrangement update")
    approval_status: Literal["pending", "approved", "rejected", "withdrawn"] = Field(
        ..., title="Current status of the WFH request"
    )
    reason_description: str = Field(..., title="Reason for the status update")
    batch_id: Optional[int] = Field(
        None, title="Unique identifier for the batch, if any"
    )  # Allow None
    requester_info: Optional[employee_schemas.EmployeeBase] = Field(
        None, exclude=True, title="Information about the requester"
    )
    supporting_doc_1: Optional[str] = Field(
        None, title="URL of the first supporting document"
    )
    supporting_doc_2: Optional[str] = Field(
        None, title="URL of the second supporting document"
    )
    supporting_doc_3: Optional[str] = Field(
        None, title="URL of the third supporting document"
    )

    class Config:
        from_attributes = True


class ArrangementQueryParams(BaseModel):
    current_approval_status: Optional[
        List[Literal["pending", "approved", "rejected", "withdrawn"]]
    ] = Field([], title="Filter by the current approval status")
    requester_staff_id: Optional[int] = Field(
        None, title="Filter by the staff ID of the requester"
    )


class ArrangementResponse(ArrangementCreateWithFile):
    arrangement_id: int = Field(..., title="Unique identifier for the arrangement")
    update_datetime: datetime = Field(
        exclude=True, title="Datetime of the arrangement update"
    )
    approval_status: Literal["pending", "approved", "rejected", "withdrawn"] = Field(
        ..., title="Current status of the WFH request", alias="current_approval_status"
    )
    approving_officer: Optional[int] = Field(
        None, title="Staff ID of the approving officer"
    )  # Allow None
    reason_description: str = Field(..., title="Reason for the status update")
    batch_id: Optional[int] = Field(
        None, title="Unique identifier for the batch, if any"
    )  # Allow None
    latest_log_id: int = Field(
        None, title="Unique identifier for the latest log entry"
    )  # Allow None
    requester_info: Optional[employee_schemas.EmployeeBase] = Field(
        None, title="Information about the requester"
    )


class ManagerPendingRequests(BaseModel):
    employee: employee_schemas.EmployeeBase
    pending_arrangements: List[ArrangementCreate]


class ManagerPendingRequestResponse(ManagerPendingRequests):
    pass
