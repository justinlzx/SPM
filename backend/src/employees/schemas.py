from pydantic import BaseModel

class EmployeeBase(BaseModel):
    staff_id: int
    staff_fname: str
    staff_lname: str
    dept: str
    country: str
    email: str
    reporting_manager: int
    role: int
    