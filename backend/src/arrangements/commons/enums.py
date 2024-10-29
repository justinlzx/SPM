from enum import Enum


class ApprovalStatus(Enum):
    PENDING_APPROVAL = "pending approval"
    PENDING_WITHDRAWAL = "pending withdrawal"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"


class Action(Enum):
    CREATE = "create"
    APPROVE = "approve"
    REJECT = "reject"
    WITHDRAW = "withdraw"
    CANCEL = "cancel"


class WfhType(Enum):
    AM = "am"
    PM = "pm"
    FULL = "full"


class RecurringFrequencyUnit(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


STATUS_ACTION_MAPPING = {
    ApprovalStatus.PENDING_APPROVAL: {
        Action.APPROVE: ApprovalStatus.APPROVED,
        Action.REJECT: ApprovalStatus.REJECTED,
        Action.CANCEL: ApprovalStatus.CANCELLED,
    },
    ApprovalStatus.APPROVED: {
        Action.WITHDRAW: ApprovalStatus.PENDING_WITHDRAWAL,
    },
    ApprovalStatus.PENDING_WITHDRAWAL: {
        Action.APPROVE: ApprovalStatus.WITHDRAWN,
        Action.REJECT: ApprovalStatus.APPROVED,
    },
    ApprovalStatus.REJECTED: {},
    ApprovalStatus.WITHDRAWN: {},
}
