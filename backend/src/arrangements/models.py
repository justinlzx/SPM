from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String

from ..database import Base


class Arrangement(Base):
    __tablename__ = "arrangements"

    arrangement_id = Column(
        Integer, primary_key=True, doc="Unique identifier for the arrangement"
    )
    last_updated_datetime = Column(
        String(length=50),
        nullable=False,
        doc="Date and time that approval status was last updated",
    )
    requester_staff_id = Column(
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=False,
        doc="Staff ID of the employee who made the request",
    )
    wfh_type = Column(
        String(length=50),
        nullable=False,
        doc="Type of WFH arrangement: full day, AM, or PM",
    )
    wfh_date = Column(
        String(length=50),
        nullable=False,
        doc="Date of the WFH arrangement",
    )
    approval_status = Column(
        String(length=50),
        nullable=False,
        doc="Status of the request: pending, approved, or rejected",
    )
    __table_args__ = (
        CheckConstraint("wfh_type IN ('full-time', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected')",
            name="check_approval_status",
        ),
    )
