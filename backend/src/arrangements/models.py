from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base


class ArrangementLog(Base):
    __tablename__ = "arrangement_logs"
    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the log entry",
    )
    log_event_datetime = Column(
        String(length=50),
        nullable=False,
        doc="Date and time of the log entry",
    )
    arrangement_id = Column(
        Integer,
        ForeignKey(
            "latest_arrangements.arrangement_id",
            use_alter=True,
            name="fk_arrangement_id",
        ),
        nullable=False,
        doc="Unique identifier for the arrangement",
    )
    batch_id = Column(
        Integer,
        ForeignKey("recurring_requests.batch_id"),
        nullable=True,
        doc="Unique identifier for the batch, if any",
    )
    log_event_staff_id = Column(
        String(length=10),
        ForeignKey("employees.staff_id"),
        nullable=False,
        doc="Staff ID of the employee who performed the action",
    )
    log_event_type = Column(
        String(length=50),
        nullable=False,
        doc="Type of the log event (create, approve, reject, withdraw, cancel)",
    )
    __table_args__ = (
        CheckConstraint(
            "log_event_type IN ('create', 'approve', 'reject', 'withdraw', 'cancel')",
            name="check_log_event_type",
        ),
    )


class LatestArrangement(Base):
    __tablename__ = "latest_arrangements"
    arrangement_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the arrangement",
    )
    update_datetime = Column(
        String(length=50),
        nullable=False,
        doc="Date and time of the latest update",
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
    current_approval_status = Column(
        String(length=50),
        nullable=False,
        doc="Current status of the request: pending, approved, rejected, or withdrawn",
    )
    approving_officer = Column(
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=True,
        doc="Staff ID of the approving officer",
    )
    reason_description = Column(
        String(length=255),
        nullable=False,
        doc="Reason for the status update",
    )
    batch_id = Column(
        Integer,
        ForeignKey("recurring_requests.batch_id"),
        nullable=True,
        doc="Unique identifier for the batch",
    )
    latest_log_id = Column(
        Integer,
        ForeignKey("arrangement_logs.log_id", use_alter=True, name="fk_latest_log_id"),
        nullable=True,
        doc="Unique identifier for the latest log entry",
    )
    requester_info = relationship(
        "Employee",
        back_populates="arrangements_requested",
        foreign_keys=[requester_staff_id],
    )
    approving_officer_info = relationship(
        "Employee",
        back_populates="arrangements_approved",
        foreign_keys=[approving_officer],
    )
    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "current_approval_status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="check_current_approval_status",
        ),
    )
    reason_description = Column(
        String(length=255),
        nullable=False,
        doc="Reason for the WFH request",
    )
    approval_reason = Column(
        String(length=255),
        nullable=True,
        doc="Reason for approval or rejection",
    )


class RecurringRequest(Base):
    __tablename__ = "recurring_requests"
    batch_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the recurring request batch",
    )
    request_datetime = Column(
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
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
    )
