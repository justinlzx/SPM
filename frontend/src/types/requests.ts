export enum ApprovalStatus {
    Approved = "approved",
    PendingApproval = "pending approval",
    PendingWithdrawal = "pending withdrawal",
    Rejected = "rejected",
    Cancelled = "cancelled",
    Withdrawn = "withdrawn",
  }

  
  
// Action types for request management
export type TAction = "approve" | "reject" | "allow withdraw" | "reject withdraw";
  
// Type for individual work-from-home requests
export type TWFHRequest = {
  staff_id: number;
  requester_info: {
    staff_fname: string;
    staff_lname: string;
    dept: string;
    position: string;
  };
  wfh_date: string;
  end_date?: string;
  wfh_type: string;
  arrangement_id: number;
  reason_description: string;
  approval_status: ApprovalStatus;
  supporting_doc_1: string;
  supporting_doc_2: string;
  supporting_doc_3: string;
};
  
// Type for grouping work-from-home requests by date
export type TArrangementsByDate = {
  date: string;
  pending_arrangements: TWFHRequest[];
};
