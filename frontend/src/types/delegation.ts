export enum DelegationStatus {
    Accepted = "accepted",
    Pending = "pending",
    Rejected = "rejected",
    Undelegated = "undelegated",
  }
  
  export type TDelegationLog = {
    manager_id: number;
    delegate_manager_id: number;
    delegate_manager_name: string;
    date_of_delegation: string;
    status_of_delegation: DelegationStatus;
  };
  
  export type TDelegationRequest = {
    date_of_delegation: string;
    full_name: string;
    staff_id: number;
    delegate_manager_id: number;
    status_of_delegation: DelegationStatus;
    reason: string;
  };
  
  export interface Peer {
    staff_id: string;
    name: string;
  }
  