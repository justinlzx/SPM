from datetime import datetime
from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from ..base import BaseSchema


class ArrangementBase(BaseSchema):
    requester_staff_id: int
    wfh_date: str
    wfh_type: Literal["full", "am", "pm"]


class ArrangementCreate(ArrangementBase):
    update_datetime: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now, exclude=True
    )
    approval_status: SkipJsonSchema[str] = Field(default="pending", exclude=True)
    reason_description: str

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
