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
        String(length=10),
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
        nullable=False,
        doc="Reason for the status update",
    )
    batch_id = Column(
        Integer,
        ForeignKey("arrangement_batches.batch_id"),
        nullable=True,
        doc="Unique identifier for the batch",
    )
    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="check_approval_status",
        ),
    )


class ArrangementBatch(Base):
    __tablename__ = "arrangement_batches"
    batch_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the batch",
    )
    update_datetime = Column(
        String(length=50),
        nullable=False,
        doc="Date and time of the log entry",
    )
    requester_staff_id = Column(
        String(length=10),
        ForeignKey("employees.staff_id"),
        nullable=False,
        doc="Staff ID of the employee who made the request",
    )
    wfh_type = Column(
        String(length=50),
        nullable=False,
        doc="Type of WFH arrangement: full day, AM, or PM",
    )
    reason_description = Column(
        String(length=255),
        nullable=False,
        doc="Reason for the status update",
    )
    start_date = Column(
        String(length=50),
        nullable=False,
        doc="Start date of the batch",
    )
    end_date = Column(
        String(length=50),
        nullable=False,
        doc="Type of the batch: full day, AM, or PM",
    )
    recurring_frequency_number = Column(
        Integer,
        nullable=False,
        doc="Numerical frequency of the recurring WFH request",
    )
    recurring_frequency_unit = Column(
        String(length=50),
        nullable=False,
        doc="Unit of the frequency of the recurring WFH request",
    )
    recurring_occurrences = Column(
        Integer,
        nullable=False,
        doc="Number of occurrences of the recurring WFH request",
    )

    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_batch_type"),
    )
