from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from pydantic.json_schema import SkipJsonSchema

from ..base import BaseSchema
from ..employees.schemas import EmployeeBase


class ArrangementBase(BaseSchema):
    staff_id: int = Field(
        ..., title="Staff ID of the employee who made the request", alias="requester_staff_id"
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

    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the request was created",
    )
    current_approval_status: SkipJsonSchema[str] = Field(
        default="pending", exclude=True, title="Approval status of the request"
    )
    approving_officer: int = Field(default=None, title="Staff ID of the approving officer")
    reason_description: str = Field(..., title="Reason for requesting the WFH")
    is_recurring: bool = Field(default=False, title="Flag to indicate if the request is recurring")
    recurring_end_date: str = Field(default=None, title="End date of a recurring WFH request")
    recurring_frequency_number: int = Field(
        default=None, title="Numerical frequency of the recurring WFH request"
    )
    recurring_frequency_unit: Literal["week", "month"] = Field(
        default=None, title="Unit of the frequency of the recurring WFH request"
    )
    recurring_occurrences: int = Field(
        default=None, title="Number of occurrences of the recurring WFH request"
    )
    batch_id: Optional[int] = Field(
        default=None, title="Unique identifier for the batch, if any"
    )  # Allow None

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Include excluded fields in the dump
        data["update_datetime"] = self.update_datetime
        data["current_approval_status"] = self.current_approval_status
        return data


class ArrangementCreateResponse(ArrangementBase):
    arrangement_id: int = Field(..., title="Unique identifier for the arrangement")
    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the request was created",
    )
    reason_description: str = Field(..., title="Reason for requesting the WFH")
    batch_id: Optional[int] = Field(
        default=None, title="Unique identifier for the batch, if any"
    )  # Allow None
    current_approval_status: str = Field(title="Approval status of the request")


class ArrangementUpdate(ArrangementBase):
    staff_id: SkipJsonSchema[int] = Field(
        None, title="Staff ID of the employee who made the request", alias="requester_staff_id"
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
    arrangement_id: int = Field(..., title="Unique identifier for the arrangement")
    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the arrangement was updated",
    )
    action: Literal["approve", "reject", "withdraw"] = Field(
        exclude=True, title="Action to be taken on the WFH request"
    )
    reason_description: str = Field(..., title="Reason for the status update")
    approving_officer: int = Field(exclude=True, title="Staff ID of the approving officer")
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
    requester_info: Optional[EmployeeBase] = Field(
        None, exclude=True, title="Information about the requester"
    )

    class Config:
        from_attributes = True


class ArrangementResponse(ArrangementLog):
    requester_info: EmployeeBase

    class Config:
        orm_mode = True


class ManagerPendingRequestsResponse(BaseModel):
    employee: EmployeeBase
    pending_arrangements: List[ArrangementCreateResponse]
