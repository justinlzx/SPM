import { green, amber, orange, red, grey, blueGrey } from "@mui/material/colors";

export enum ApprovalStatus {
  PendingApproval = "pending approval",
  PendingWithdrawal = "pending withdrawal",
  Approved = "approved",
  Rejected = "rejected",
  Cancelled = "cancelled",
  Withdrawn = "withdrawn",
}

export enum Action {
  Approve = "approve",
  Reject = "reject",
  Withdraw = "withdraw",
  Cancel = "cancel",
}

export const STATUS_ACTION_MAPPING: Record<
  ApprovalStatus,
  Partial<Record<Action, ApprovalStatus>>
> = {
  [ApprovalStatus.PendingApproval]: {
    [Action.Approve]: ApprovalStatus.Approved,
    [Action.Reject]: ApprovalStatus.Rejected,
    [Action.Cancel]: ApprovalStatus.Cancelled,
  },
  [ApprovalStatus.Approved]: {
    [Action.Withdraw]: ApprovalStatus.PendingWithdrawal,
  },
  [ApprovalStatus.PendingWithdrawal]: {
    [Action.Approve]: ApprovalStatus.Withdrawn,
    [Action.Reject]: ApprovalStatus.Approved,
  },
  [ApprovalStatus.Rejected]: {},
  [ApprovalStatus.Withdrawn]: {},
  [ApprovalStatus.Cancelled]: {},
};


export const ApprovalStatusColors: Record<ApprovalStatus, string> = {
  [ApprovalStatus.Approved]: green[500],           
  [ApprovalStatus.PendingApproval]: amber[500],    
  [ApprovalStatus.PendingWithdrawal]: orange[500], 
  [ApprovalStatus.Rejected]: red[500],            
  [ApprovalStatus.Cancelled]: grey[500],
  [ApprovalStatus.Withdrawn]: blueGrey[500],       
};
