import { green, amber, orange, red, grey, blueGrey } from "@mui/material/colors";

export enum ApprovalStatus {
  Approved = "approved",
  PendingApproval = "pending approval",
  PendingWithdrawal = "pending withdrawal",
  Rejected = "rejected",
  Cancelled = "cancelled",
  Withdrawn = "withdrawn",
}

export const ApprovalStatusColors: Record<ApprovalStatus, string> = {
  [ApprovalStatus.Approved]: green[500],           
  [ApprovalStatus.PendingApproval]: amber[500],    
  [ApprovalStatus.PendingWithdrawal]: orange[500], 
  [ApprovalStatus.Rejected]: red[500],            
  [ApprovalStatus.Cancelled]: grey[500],
  [ApprovalStatus.Withdrawn]: blueGrey[500],       
};
