import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/ApprovalStatus";  
import { Filters } from "../../components/Filters";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const mapApprovalStatus = (status: string): ApprovalStatus => {
  switch (status.toLowerCase()) {
    case "approved":
      return ApprovalStatus.Approved;
    case "pending approval":
      return ApprovalStatus.PendingApproval;
    case "pending withdrawal":
      return ApprovalStatus.PendingWithdrawal;
    case "rejected":
      return ApprovalStatus.Rejected;
    case "cancelled":
      return ApprovalStatus.Cancelled;
    case "withdrawn":
      return ApprovalStatus.Withdrawn;
    default:
      throw new Error(`Unknown approval status: ${status}`);
  }
};

type TWFHRequest = {
  arrangement_id: number;
  staff_id: number;
  wfh_date: string;
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  approval_status: ApprovalStatus; 
  work_type: string; // Added work_type field here
};

export const MyWfhSchedulePage: React.FC = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");

  const { user } = useContext(UserContext);
  const userId = user!.id;

  useEffect(() => {
    const fetchRequests = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );
        const allRequests: TWFHRequest[] = response.data.data.map((request: any) => ({
          ...request,
          approval_status: mapApprovalStatus(request.approval_status), 
        }));
        console.log(allRequests);
        setRequests(allRequests);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };


    fetchWFHRequests();
  }, [user, userId]);

  const handleApplyFilters = (filters: {
    startDate: Date | null;
    endDate: Date | null;
    wfhType: string;
    requestStatus: string[];
    wfhDuration: string; 
  }) => {
    // Logic to apply the filters to your request data
    console.log("Applied Filters:", filters);

    const filteredRequests = requests.filter((request) => {
      if (filters.startDate && new Date(request.wfh_date) < filters.startDate) return false;
      if (filters.endDate && new Date(request.wfh_date) > filters.endDate) return false;
      if (filters.wfhType && request.wfh_type !== filters.wfhType) return false;
      if (filters.requestStatus.length > 0 && !filters.requestStatus.includes(request.approval_status.toString())) return false;

      return true;
    });

    setRequests(filteredRequests);
  };

  // Update state when an action is successful (cancel/withdraw)
  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    const updatedStatus = action === "cancel" ? ApprovalStatus.Cancelled : ApprovalStatus.PendingWithdrawal;

    setRequests((prevRequests) =>
      prevRequests.map((request) =>
        request.arrangement_id === id
          ? { ...request, approval_status: updatedStatus } 
          : request 
      )
    );

    setSnackbarMessage(
      action === "cancel"
        ? "Your WFH request has been successfully cancelled!"
        : "Withdrawal Request has been sent to your manager for review."
    );
    setOpenSnackbar(true);
  };

  const handleCloseSnackBar = () => setOpenSnackbar(false);

  return (
    <Container sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My WFH Request Overview
      </Typography>

      <Filters 
        onApply={handleApplyFilters} 
      />
      <WFHRequestTable requests={requests} handleSuccess={handleSuccess} />

      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackBar}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert onClose={handleCloseSnackBar} severity="success">
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};


export default MyWfhSchedulePage;
