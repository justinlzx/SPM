from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String

from ..database import Base


class ArrangementLog(Base):
    __tablename__ = "arrangement_logs"
    arrangement_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the arrangement",
    )
    update_datetime = Column(
        String(length=50),
        nullable=False,
        doc="Date and time of the log entry",
    )
    requester_staff_id = Column(
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=False,
        doc="Staff ID of the employee who made the request",
    )
    wfh_date = Column(
        String(length=50),
        nullable=False,
        doc="Date of the WFH arrangement",
    )
    wfh_type = Column(
        String(length=50),
        nullable=False,
        doc="Type of WFH arrangement: full day, AM, or PM",
    )
    approval_status = Column(
        String(length=50),
        nullable=False,
        doc="Status of the request: pending, approved, rejected, or withdrawn",
    )
    reason_description = Column(
        String(length=255),
        nullable=True,
        doc="Reason for the status update",
    )
    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="check_approval_status",
        ),
    )
