from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import utils
from ..database import get_db
from ..employees.models import Employee
from ..employees.schemas import EmployeeBase, EmployeePeerResponse
from . import exceptions, models, schemas, services

router = APIRouter()


@router.get("/manager/peermanager/{staff_id}", response_model=EmployeePeerResponse)
def get_reporting_manager_and_peer_employees(staff_id: int, db: Session = Depends(get_db)):
    """Get the reporting manager and peer employees of an employee by their staff_id.

    If the employee reports to themselves, the manager will be set to None.
    """
    try:
        # Get manager
        manager: models.Employee = services.get_manager_by_employee_staff_id(db, staff_id)

        # Get list of peer employees
        peer_employees: List[models.Employee] = services.get_employees_by_manager_id(
            db, manager.staff_id
        )

        # Convert peer employees to Pydantic model
        peer_employees_pydantic: List[schemas.EmployeeBase] = (
            utils.convert_model_to_pydantic_schema(peer_employees, schemas.EmployeeBase)
        )

        print(f"Num results: {len(peer_employees)}")

        # Format to response model
        response = schemas.EmployeePeerResponse(
            manager_id=manager.staff_id, peer_employees=peer_employees_pydantic
        )

        return response
    except exceptions.EmployeeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except exceptions.ManagerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{staff_id}", response_model=EmployeeBase)
def get_employee_by_staff_id(staff_id: int, db: Session = Depends(get_db)):
    """Get an employee by staff_id."""
    try:
        employee = services.get_employee_by_staff_id(db, staff_id)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/email/{email}", response_model=EmployeeBase)
def get_employee_by_email(email: str, db: Session = Depends(get_db)):
    """Get an employee by email."""
    try:
        employee = services.get_employee_by_email(db, email)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/manager/employees/{staff_id}", response_model=List[EmployeeBase])
def get_employees_under_manager(staff_id: int, db: Session = Depends(get_db)):
    """Get a list of employees under a specific manager by their staff_id."""
    try:
        # Get employees that report to the given employee
        employees_under_manager: List[Employee] = services.get_employees_by_manager_id(db, staff_id)

        # Convert the list of employees to Pydantic model
        employees_under_manager_pydantic = utils.convert_model_to_pydantic_schema(
            employees_under_manager, EmployeeBase
        )

        return employees_under_manager_pydantic
    except exceptions.ManagerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


# Load the employee data from CSV
# CSV_FILE_PATH = os.path.join("src", "init_db", "employee.csv")  # Adjust the path as necessary
# employee_df = pd.read_csv(CSV_FILE_PATH)

# @router.get("/get_staff_id/email")
# async def get_staff_id(email: str) -> JSONResponse:
#     try:
#         # Find the staff ID for the given email
#         employee_record = employee_df[employee_df["Email"] == email]  # Use the correct column

#         if not employee_record.empty:
#             # Convert the staff_id to a native Python int
#             staff_id = int(employee_record["Staff_ID"].values[0])  # Convert to int
#             return JSONResponse(content={"staff_id": staff_id})
#         else:
#             raise HTTPException(status_code=404, detail="Employee not found")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
