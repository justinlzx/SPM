from pydantic import BaseModel
from typing import Optional, List


class EmployeeBase(BaseModel):
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

    class Config:
        from_attributes = (
            True
        )


class EmployeePeerResponse(BaseModel):
    manager_id: Optional[int]
    peer_employees: List[EmployeeBase]  # Use the Pydantic model for peer employees

    class Config:
        from_attributes = True
