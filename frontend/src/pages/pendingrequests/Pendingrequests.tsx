import React, { useEffect, useState } from "react";
import axios from "axios";
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define the type for the requests, based on your API response
type Request = {
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  update_datetime: string;
  approval_status: string;
  reason_description: string;
  batch_id: string | null;
};

const PendingRequests = () => {
  const [requests, setRequests] = useState<Request[]>([]);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view`);  // Use backticks for template literal
        setRequests(response.data);  // Set requests data
      } catch (error) {
        console.error("Error fetching requests:", error);
      }
    };

    fetchRequests();  // Fetch requests when component mounts
  }, []);

  return (
    <div>
      <h2>Pending Requests</h2>
      <table>
        <thead>
          <tr>
            <th>Requester Staff ID</th>
            <th>WFH Date</th>
            <th>WFH Type</th>
            <th>Approval Status</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => (
            <tr key={request.arrangement_id}>
              <td>{request.requester_staff_id}</td>
              <td>{request.wfh_date}</td>
              <td>{request.wfh_type}</td>
              <td>{request.approval_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PendingRequests;
