from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, Field

from ..base import BaseSchema


class ArrangementBase(BaseSchema):
    last_updated_datetime: datetime = Field(
        default_factory=datetime.now,
        validation_alias=AliasChoices("request_created_datetime"),
    )
    requester_staff_id: int
    wfh_date: str
    wfh_type: Literal["full", "am", "pm"]
    approval_status: Literal["pending", "approved", "rejected"]


class WFHRequestCreateBody(ArrangementBase):
    approval_status: Literal["pending"]  # Default to pending


# class WFHRequestCreateResponse(ArrangementBase):
#     arrangement_id: int
