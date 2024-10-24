from datetime import datetime
from typing import List, Optional

from ..base import BaseSchema
from ..employees.models import DelegationStatus


class EmployeeBase(BaseSchema):
    staff_id: int
    staff_fname: str
    staff_lname: str
    dept: str
    position: str
    country: str
    email: str
    reporting_manager: Optional[int] = None  # Optional for cases where there is no manager
    role: int


class EmployeePeerResponse(BaseSchema):
    manager_id: Optional[int]
    peer_employees: List[EmployeeBase]  # Use the Pydantic model for peer employees


class DelegateLogCreate(BaseSchema):
    manager_id: int
    delegate_manager_id: int
    date_of_delegation: datetime
    status_of_delegation: Optional[DelegationStatus] = (
        DelegationStatus.pending
    )  # Default to pending

    class Config:
        from_attributes = True
