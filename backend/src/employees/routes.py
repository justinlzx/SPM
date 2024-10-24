from datetime import datetime
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from .. import utils
from ..arrangements import models as arrangement_models
from ..database import get_db
from ..email.routes import send_email
from ..employees import services as employee_services
from ..employees.models import DelegateLog, DelegationStatus, Employee
from ..employees.schemas import DelegateLogCreate, EmployeeBase, EmployeePeerResponse
from ..notifications.email_notifications import craft_email_content_for_delegation
from . import exceptions, models, schemas, services

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


@router.post("/manager/delegate/{staff_id}", response_model=DelegateLogCreate)
async def delegate_manager(staff_id: int, delegate_manager_id: int, db: Session = Depends(get_db)):
    """
    Delegates the approval responsibility of a manager to another staff member.
    Logs the delegation in `delegate_logs` but does not update pending approvals.

    If the person requesting or the delegatee is already in the `delegate_logs`,
    the request will fail.
    """
    # Step 1: Check if either the staff_id or delegate_manager_id is already in `delegate_logs`
    existing_delegation = (
        db.query(DelegateLog)
        .filter(
            (DelegateLog.manager_id == staff_id)
            | (DelegateLog.delegate_manager_id == delegate_manager_id)
        )
        .filter(
            DelegateLog.status_of_delegation.in_(
                [DelegationStatus.pending, DelegationStatus.accepted]
            )
        )
        .first()
    )

    if existing_delegation:
        raise HTTPException(
            status_code=400,
            detail="Delegation already exists for either the manager or delegatee.",
        )

    # Step 2: Log the delegation in the `delegate_logs` table
    try:
        new_delegation = DelegateLog(
            manager_id=staff_id,
            delegate_manager_id=delegate_manager_id,
            date_of_delegation=datetime.utcnow(),
            status_of_delegation=DelegationStatus.pending,  # Default to pending
        )

        db.add(new_delegation)
        db.commit()
        db.refresh(new_delegation)

        # Step 3: Fetch employee info for both manager and delegatee
        manager_employee = employee_services.get_employee_by_id(db, staff_id)
        delegatee_employee = employee_services.get_employee_by_id(db, delegate_manager_id)

        # Step 4: Craft and send email notifications to both the manager and delegatee
        manager_subject, manager_content = craft_email_content_for_delegation(
            manager_employee, delegatee_employee, "delegate"
        )
        await send_email(manager_employee.email, manager_subject, manager_content)

        delegatee_subject, delegatee_content = craft_email_content_for_delegation(
            delegatee_employee, manager_employee, "delegated_to"
        )
        await send_email(delegatee_employee.email, delegatee_subject, delegatee_content)

        return new_delegation  # Returning the created delegation log

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class DelegationApprovalStatus(Enum):
    accept = "accepted"
    reject = "rejected"


@router.put("/manager/delegate/{staff_id}/status", response_model=DelegateLogCreate)
async def update_delegation_status(
    staff_id: int,
    status: DelegationApprovalStatus,
    db: Session = Depends(get_db),
):
    """
    Updates the status of a delegation request (accepted or rejected).
    If accepted, updates the approving officer in the `latest_arrangements` table for pending requests.

    :param staff_id: The ID of the staff (delegate) whose delegation status is being updated.
    :param status: The status of the delegation (either 'accepted' or 'rejected').
    :param db: The database session.
    :return: Updated delegation log.
    """
    try:
        # Fetch the delegation log entry for the given staff_id (delegate manager)
        delegation_log = (
            db.query(DelegateLog).filter(DelegateLog.delegate_manager_id == staff_id).first()
        )

        if not delegation_log:
            raise HTTPException(status_code=404, detail="Delegation log not found.")

        # Fetch manager and delegatee details for email notification
        manager_employee = employee_services.get_employee_by_id(db, delegation_log.manager_id)
        delegatee_employee = employee_services.get_employee_by_id(db, staff_id)

        if status == DelegationApprovalStatus.accept:
            delegation_log.status_of_delegation = DelegationStatus.accepted

            # Step 2: Update pending approval requests in `latest_arrangements`
            pending_arrangements = (
                db.query(arrangement_models.LatestArrangement)
                .filter(
                    arrangement_models.LatestArrangement.approving_officer
                    == delegation_log.manager_id,
                    arrangement_models.LatestArrangement.current_approval_status.in_(
                        ["pending approval", "pending withdrawal"]
                    ),
                )
                .all()
            )

            for arrangement in pending_arrangements:
                arrangement.delegate_approving_officer = delegation_log.delegate_manager_id
                db.add(arrangement)

            db.commit()

            # Send email to staff for approval
            staff_subject, staff_content = craft_email_content_for_delegation(
                manager_employee, delegatee_employee, "approved"
            )
            await send_email(manager_employee.email, staff_subject, staff_content)

            # Send email to delegate for approval
            delegate_subject, delegate_content = craft_email_content_for_delegation(
                delegatee_employee, manager_employee, "approved_for_delegate"
            )
            await send_email(delegatee_employee.email, delegate_subject, delegate_content)

        elif status == DelegationApprovalStatus.reject:
            delegation_log.status_of_delegation = DelegationStatus.rejected

            # Send email to staff for rejection
            staff_subject, staff_content = craft_email_content_for_delegation(
                manager_employee, delegatee_employee, "rejected"
            )
            await send_email(manager_employee.email, staff_subject, staff_content)

            # Send email to delegate for rejection
            delegate_subject, delegate_content = craft_email_content_for_delegation(
                delegatee_employee, manager_employee, "rejected_for_delegate"
            )
            await send_email(delegatee_employee.email, delegate_subject, delegate_content)

        db.commit()
        db.refresh(delegation_log)

        return delegation_log
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/manager/undelegate/{staff_id}", response_model=DelegateLogCreate)
async def undelegate_manager(staff_id: int, db: Session = Depends(get_db)):
    try:
        # Step 1: Fetch the delegation log entry for the given staff_id (manager who initiated the delegation)
        delegation_log = db.query(DelegateLog).filter(DelegateLog.manager_id == staff_id).first()

        if not delegation_log:
            raise HTTPException(status_code=404, detail="Delegation log not found.")

        # Fetch manager and delegatee details for email notification
        manager_employee = employee_services.get_employee_by_id(db, delegation_log.manager_id)
        delegatee_employee = employee_services.get_employee_by_id(
            db, delegation_log.delegate_manager_id
        )

        # Step 2: Check if the status of the delegation is 'accepted'
        if delegation_log.status_of_delegation != DelegationStatus.accepted:
            raise HTTPException(
                status_code=400, detail="Delegation must be approved to undelegate."
            )

        # Step 3: Update the `latest_arrangements` to remove the delegation and restore the original manager
        pending_arrangements = (
            db.query(arrangement_models.LatestArrangement)
            .filter(
                arrangement_models.LatestArrangement.delegate_approving_officer
                == delegation_log.delegate_manager_id,
                arrangement_models.LatestArrangement.current_approval_status == "pending",
            )
            .all()
        )

        for arrangement in pending_arrangements:
            arrangement.delegate_approving_officer = None  # Remove the delegate manager
            db.add(arrangement)

        # Step 4: Mark the delegation as 'undelegated' (new status)
        delegation_log.status_of_delegation = DelegationStatus.undelegated

        # Step 5: Commit the changes to the database
        db.commit()
        db.refresh(delegation_log)

        # Send email to the manager informing them that the delegation has been withdrawn
        manager_subject, manager_content = craft_email_content_for_delegation(
            manager_employee, delegatee_employee, "withdrawn"
        )
        await send_email(manager_employee.email, manager_subject, manager_content)

        # Send email to the delegatee informing them that the delegation has been withdrawn
        delegatee_subject, delegatee_content = craft_email_content_for_delegation(
            delegatee_employee, manager_employee, "withdrawn_for_delegate"
        )
        await send_email(delegatee_employee.email, delegatee_subject, delegatee_content)

        return delegation_log

    except HTTPException as http_exc:
        # Log HTTPException details and re-raise it
        print(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Log any unexpected errors and raise 500
        print(f"Unexpected error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
