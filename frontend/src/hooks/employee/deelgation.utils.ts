// delegation.utils.ts
import axios from "axios";
import { TDelegationLog, TDelegationRequest, Peer, DelegationStatus } from "../../types/delegation";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Fetch list of peers for delegation
export const fetchPeers = async (userId: string): Promise<Peer[]> => {
  return response.data.peer_employees
    .filter((peer: any) => peer.staff_id !== userId)
    .map((peer: any) => ({
      staff_id: peer.staff_id,
      name: `${peer.staff_fname} ${peer.staff_lname}`,
    }));
};

// Fetch delegation logs for the user
export const fetchDelegationLogs = async (userId: string): Promise<TDelegationLog[]> => {
  const response = await axios.get(`${BACKEND_URL}/employees/manager/viewalldelegations/${userId}`);
  return response.data.sent_delegations || [];
};

// Send a new delegation request
export const sendDelegationRequest = async (userId: string, delegateManagerId: string): Promise<TDelegationLog> => {
  const response = await axios.post(`${BACKEND_URL}/employees/manager/delegate/${userId}`, null, {
    params: { delegate_manager_id: delegateManagerId },
  });
  return {
    manager_id: response.data.manager_id,
    delegate_manager_id: response.data.delegate_manager_id,
    delegate_manager_name: response.data.delegate_manager_name,
    date_of_delegation: response.data.date_of_delegation,
    status_of_delegation: response.data.status_of_delegation,
  };
};

// Cancel a delegation
export const cancelDelegation = async (userId: string, delegateManagerId: number): Promise<void> => {
  await axios.put(`${BACKEND_URL}/employees/manager/undelegate/${userId}`, {
    params: { delegate_manager_id: delegateManagerId },
  });
};

// Fetch pending delegation requests
export const fetchPendingDelegations = async (userId: string): Promise<TDelegationRequest[]> => {
  const response = await axios.get(`${BACKEND_URL}/employees/manager/viewdelegations/${userId}`, {
    params: { status: "pending" },
  });
  return response.data.pending_approval_delegations || [];
};

// Handle accept/reject action for a delegation request
export const handleDelegationAction = async (
  action: "accepted" | "rejected",
  staffId: number,
  reason?: string
): Promise<void> => {
  await axios.put(`${BACKEND_URL}/employees/manager/delegate/${staffId}/status`, { description: reason }, {
    params: { status: action },
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};
