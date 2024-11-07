from ...arrangements.commons.enums import Action, ApprovalStatus

ARRANGEMENT_SUBJECT = {
    "employee": {
        Action.CREATE: "Your WFH Request Has Been Created",
        Action.APPROVE: {
            ApprovalStatus.APPROVED: "Your WFH Request Has Been Approved",
            ApprovalStatus.WITHDRAWN: "Your WFH Request Has Been Withdrawn",
        },
        Action.REJECT: {
            ApprovalStatus.REJECTED: "Your WFH Request Has Been Rejected",
            ApprovalStatus.APPROVED: "Your WFH Request Withdrawal Has Been Rejected",
        },
        Action.WITHDRAW: "You Have Requested to Withdraw Your WFH",
        Action.CANCEL: "Your WFH Request Has Been Cancelled",  # Added entry
    },
    "manager": {
        Action.CREATE: "Your Staff Created a WFH Request",
        Action.APPROVE: {
            ApprovalStatus.APPROVED: "You Have Approved a WFH Request",
            ApprovalStatus.WITHDRAWN: "You Have Approved a WFH Request Withdrawal",
        },
        Action.REJECT: {
            ApprovalStatus.REJECTED: "You Have Rejected a WFH Request",
            ApprovalStatus.APPROVED: "You Have Rejected a WFH Request Withdrawal",
        },
        Action.WITHDRAW: "Your Staff Has Requested to Withdraw Their WFH",
        Action.CANCEL: "A Staff Member's WFH Request Has Been Cancelled",  # Added entry
    },
}


DELEGATION_SUBJECT = {
    "delegator": {
        "delegate": "You have delegated approval responsibilities",
        "undelegate": "Approval responsibilities have been returned to you",
        "approved": "Your delegation request has been approved",
        "rejected": "Your delegation request has been rejected",
        "withdrawn": "Your delegation request has been withdrawn",
    },
    "delegatee": {
        "delegate": "Approval responsibilities delegated to you",
        "undelegate": "Approval responsibilities have been returned",
        "approved": "You have approved a delegation request",
        "rejected": "You have rejected a delegation request",
        "withdrawn": "Your delegation has been withdrawn",
    },
}
