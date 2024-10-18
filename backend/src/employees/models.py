from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from src.arrangements.models import LatestArrangement


from ..database import Base


class Employee(Base):
    __tablename__ = "employees"

    staff_id = Column(Integer, primary_key=True)
    staff_fname = Column(String(length=50), nullable=False)
    staff_lname = Column(String(length=50), nullable=False)
    dept = Column(String(length=50), nullable=False)
    position = Column(String(length=50), nullable=False)
    country = Column(String(length=50), nullable=False)
    email = Column(String, ForeignKey("auth.email"), unique=True, nullable=False)
    reporting_manager = Column(Integer, ForeignKey("employees.staff_id"), nullable=True)
    role = Column(Integer, CheckConstraint("role IN (1, 2, 3)"), nullable=False)

    manager = relationship("Employee", remote_side=[staff_id], lazy="select")
    auth_info = relationship("Auth", back_populates="employee")

    arrangement_logs_requested = relationship(
        "ArrangementLog",
        foreign_keys="[ArrangementLog.requester_staff_id]",
        back_populates="requester_info",
        lazy="select",
    )
    arrangement_logs_approved = relationship(
        "ArrangementLog",
        foreign_keys="[ArrangementLog.approving_officer]",
        back_populates="approving_officer_info",
        lazy="select",
    )
    latest_arrangements_requested = relationship(
        "LatestArrangement",
        foreign_keys="[LatestArrangement.requester_staff_id]",
        back_populates="requester_info",
        lazy="select",
    )
    latest_arrangements_approved = relationship(
        "LatestArrangement",
        foreign_keys="[LatestArrangement.approving_officer]",
        back_populates="approving_officer_info",
        lazy="select",
    )


class DelegationStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    undelegated = "undelegated"


class DelegateLog(Base):
    __tablename__ = "delegate_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_id = Column(Integer, ForeignKey("employees.staff_id"), nullable=False)
    delegate_manager_id = Column(Integer, ForeignKey("employees.staff_id"), nullable=False)
    update_datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date_of_delegation = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_of_delegation = Column(
        Enum(DelegationStatus), nullable=False, default=DelegationStatus.pending
    )
    description = Column(String(length=255), nullable=True)

    # Relationships to the Employee model
    manager = relationship(
        "Employee",
        foreign_keys=[manager_id],
        back_populates="delegations_as_manager",
        lazy="select",
    )
    delegator = relationship(
        "Employee",
        foreign_keys=[delegate_manager_id],
        back_populates="delegations_as_delegator",
        lazy="select",
    )


# Add the relationships to the Employee class
Employee.delegations_as_manager = relationship(
    "DelegateLog",
    foreign_keys=[DelegateLog.manager_id],
    back_populates="manager",
    lazy="select",
)

Employee.delegations_as_delegator = relationship(
    "DelegateLog",
    foreign_keys=[DelegateLog.delegate_manager_id],
    back_populates="delegator",
    lazy="select",
)
# if __name__ == "__main__":

#     session = Session(bind=engine)

#     director = Employee(
#         staff_id=3,
#         staff_fname="Johnson",
#         staff_lname="Doe",
#         email="johnson.doe@test.com",
#         dept="IT",
#         position="Director",
#         country="USA",
#         role=2,
#     )

#     session.add(director)
#     session.commit()

#     manager = Employee(
#         staff_id=1,
#         staff_fname="Jane",
#         staff_lname="Smith",
#         email="jane.smith@test.com",
#         dept="IT",
#         position="Manager",
#         country="USA",
#         role=2,
#         reporting_manager=3,
#     )

#     session.add(manager)
#     session.commit()

#     employee = Employee(
#         staff_fname="John",
#         staff_lname="Doe",
#         email="john.doe@test.com",
#         dept="IT",
#         position="Manager",
#         country="USA",
#         reporting_manager=1,
#         role=3,
#     )

#     session.add(employee)
#     session.commit()

#     session.refresh(employee)

#     # Print the manager object
#     print(employee.manager.staff_fname)
#     print(manager.manager.staff_fname)

#     # Close the session
#     session.close()
