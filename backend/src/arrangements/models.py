from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, DateTime
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
    update_datetime = Column(
        DateTime,
        nullable=False,
        doc="Date and time of the update",
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
        default="pending",
        doc="Current status of the request: pending, approved, rejected, withdrawn or cancelled",
    )
    approving_officer = Column(
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=True,
        doc="Staff ID of the approving officer",
    )
    reason_description = Column(
        String(length=255),
        nullable=True,
        doc="Reason for the WFH request",
    )
    batch_id = Column(
        Integer,
        nullable=True,
        doc="Unique identifier for the batch, if any",
    )
    supporting_doc_1 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the first supporting document",
    )
    supporting_doc_2 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the second supporting document",
    )
    supporting_doc_3 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the third supporting document",
    )

    requester_info = relationship(
        "Employee",
        foreign_keys=[requester_staff_id],
        back_populates="arrangement_logs_requested",
    )
    approving_officer_info = relationship(
        "Employee",
        foreign_keys=[approving_officer],
        back_populates="arrangement_logs_approved",
    )

    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected', 'withdrawn', 'cancelled')",
            name="check_approval_status",
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
    current_approval_status = Column(
        String(length=50),
        nullable=False,
        doc="Current status of the request: pending, approved, rejected, withdrawn or cancelled",
    )
    approving_officer = Column(
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=True,
        doc="Staff ID of the approving officer",
    )
    delegate_approving_officer = Column(  # New column
        Integer,
        ForeignKey("employees.staff_id"),
        nullable=True,
        doc="Staff ID of the delegate approving officer",
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
        back_populates="latest_arrangements_requested",
        foreign_keys=[requester_staff_id],
        lazy="select",
    )
    approving_officer_info = relationship(
        "Employee",
        back_populates="latest_arrangements_approved",
        foreign_keys=[approving_officer],
        lazy="select",
    )
    delegate_approving_officer_info = relationship(  # New relationship for delegate
        "Employee",
        foreign_keys=[delegate_approving_officer],
        lazy="select",
    )
    supporting_doc_1 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the first supporting document",
    )
    supporting_doc_2 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the second supporting document",
    )
    supporting_doc_3 = Column(
        String(length=255),
        nullable=True,
        doc="URL of the third supporting document",
    )
    status_reason = Column(
        String(length=255),
        nullable=True,
        doc="Reason for approval or rejection",
    )
    __table_args__ = (
        CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),
        CheckConstraint(
            "current_approval_status IN ('pending', 'approved', 'rejected', 'withdrawn', 'cancelled')",
            name="check_current_approval_status",
        ),
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

    __table_args__ = (CheckConstraint("wfh_type IN ('full', 'am', 'pm')", name="check_wfh_type"),)
