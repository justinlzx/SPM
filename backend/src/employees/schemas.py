from typing import List, Optional

from ..base import BaseSchema


class EmployeeBase(BaseSchema):
    staff_id: int
    staff_fname: str
    staff_lname: str
    dept: str
    position: str
    country: str
    email: str
    reporting_manager: Optional[int] = (
        None  # Optional for cases where there is no manager
    )
    role: int


class EmployeePeerResponse(BaseSchema):
    manager_id: Optional[int]
    peer_employees: List[EmployeeBase]  # Use the Pydantic model for peer employees
