from datetime import datetime
from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from ..base import BaseSchema


class ArrangementBase(BaseSchema):
    requester_staff_id: int = Field(
        ..., title="Staff ID of the employee who made the request"
    )
    wfh_date: str = Field(
        ...,
        title="Date of an adhoc WFH request or the start date of a recurring WFH request",
    )
    wfh_type: Literal["full", "am", "pm"] = Field(..., title="Type of WFH arrangement")


class ArrangementCreate(ArrangementBase):
    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
        exclude=True,
        title="Datetime that the request was created",
    )
    approval_status: SkipJsonSchema[str] = Field(
        default="pending", exclude=True, title="Approval status of the request"
    )
    reason_description: str = Field(..., title="Reason for requesting the WFH")
    is_recurring: bool = Field(
        default=False, title="Flag to indicate if the request is recurring"
    )
    recurring_end_date: str = Field(
        default=None, title="End date of a recurring WFH request"
    )
    recurring_frequency_number: int = Field(
        default=None, title="Numerical frequency of the recurring WFH request"
    )
    recurring_frequency_unit: Literal["week", "month"] = Field(
        default=None, title="Unit of the frequency of the recurring WFH request"
    )
    recurring_occurrences: int = Field(
        default=None, title="Number of occurrences of the recurring WFH request"
    )

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Include excluded fields in the dump
        data["update_datetime"] = self.update_datetime
        data["approval_status"] = self.approval_status
        return data


# class ArrangementLog(ArrangementBase):
#     arrangement_id = Field("arrangement_id")
#     update_datetime: datetime = Field(default_factory=datetime.now)
#     approval_status: Literal["pending", "approved", "rejected", "withdrawn"]
#     reason_description: str


# class ArrangementSnapshot(ArrangementLog):
#     arrangement_id: int
#     update_datetime: datetime
#     reason_description: str
#     approval_status: Literal["pending", "approved", "rejected", "withdrawn"]
