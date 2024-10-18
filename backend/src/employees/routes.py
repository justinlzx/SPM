from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from .. import utils
from ..database import get_db
from ..employees.models import Employee
from ..employees.schemas import EmployeeBase, EmployeePeerResponse, DelegateLogCreate
from . import exceptions, models, schemas, services
from ..arrangements import models as arrangement_models, services as arrangement_services
from ..employees import models as employee_models

router = APIRouter()


@router.get("/manager/peermanager/{staff_id}", response_model=EmployeePeerResponse)
def get_reporting_manager_and_peer_employees(staff_id: int, db: Session = Depends(get_db)):
    """Get the reporting manager and peer employees of an employee by their staff_id.

    If the employee reports to themselves, the manager will be set to None.
    """

    # Auto Approve for Jack Sim and Skip manager check
    if staff_id == 130002:
        return EmployeePeerResponse(manager_id=None, peer_employees=[])

    try:
        # Get manager
        manager: models.Employee = services.get_manager_by_subordinate_id(db, staff_id)

        if not manager:
            return EmployeePeerResponse(manager_id=None, peer_employees=[])

        # Get list of peer employees
        peer_employees: List[models.Employee] = services.get_subordinates_by_manager_id(
            db, manager.staff_id
        )

        # Filter out the manager from the peer employees
        peer_employees = [peer for peer in peer_employees if peer.staff_id != manager.staff_id]

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
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{staff_id}", response_model=EmployeeBase)
def get_employee_by_staff_id(staff_id: int, db: Session = Depends(get_db)):
    """Get an employee by staff_id."""
    try:
        employee = services.get_employee_by_id(db, staff_id)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/email/{email}", response_model=EmployeeBase)
def get_employee_by_email(email: EmailStr, db: Session = Depends(get_db)):
    """Get an employee by email."""
    try:
        employee = services.get_employee_by_email(db, email)
        return employee  # Pydantic model (EmployeeBase) will handle serialization
    except exceptions.EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/manager/employees/{staff_id}", response_model=List[EmployeeBase])
def get_subordinates_by_manager_id(staff_id: int, db: Session = Depends(get_db)):
    """Get a list of employees under a specific manager by their staff_id."""
    try:
        # Get employees that report to the given employee
        employees_under_manager: List[Employee] = services.get_subordinates_by_manager_id(
            db, staff_id
        )

        # Convert the list of employees to Pydantic model
        employees_under_manager_pydantic = utils.convert_model_to_pydantic_schema(
            employees_under_manager, EmployeeBase
        )

        return employees_under_manager_pydantic
    except exceptions.ManagerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/manager/delegate/{staff_id}", response_model=DelegateLogCreate)
def delegate_manager(staff_id: int, delegate_manager_id: int, db: Session = Depends(get_db)):
    """
    Delegates the approval responsibility of a manager to another staff member.
    Logs the delegation in `delegate_logs` and updates pending arrangements.

    :param staff_id: The staff ID of the manager initiating the delegation.
    :param delegate_manager_id: The staff ID of the delegated manager.
    :param db: The database session.
    :return: Details of the created delegation log entry.
    """
    # Step 1: Log the delegation in the `delegate_logs` table
    try:
        # Create a new DelegateLog record
        new_delegation = employee_models.DelegateLog(
            manager_id=staff_id,
            delegate_manager_id=delegate_manager_id,
            date_of_delegation=datetime.utcnow(),
            status_of_delegation=employee_models.DelegationStatus.pending,  # Default status
        )

        db.add(new_delegation)
        db.commit()
        db.refresh(new_delegation)

        # Step 2: Update pending approval requests in `latest_arrangements`
        # Fetch all pending requests where staff_id is the approving officer
        pending_arrangements = (
            db.query(arrangement_models.LatestArrangement)
            .filter(
                arrangement_models.LatestArrangement.approving_officer == staff_id,
                arrangement_models.LatestArrangement.current_approval_status == "pending",
            )
            .all()
        )

        if not pending_arrangements:
            raise HTTPException(status_code=404, detail="No pending arrangements found.")

        # Update the approving officer to the delegate_manager_id
        for arrangement in pending_arrangements:
            arrangement.delegate_approving_officer = delegate_manager_id
            db.add(arrangement)

        db.commit()

        return new_delegation  # Returning the created delegation log
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


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
