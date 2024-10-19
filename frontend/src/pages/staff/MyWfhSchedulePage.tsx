import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/ApprovalStatus";  

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
  approval_status: ApprovalStatus; // Only using approval_status
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
          approval_status: mapApprovalStatus(request.approval_status), // Ensure mapping here
        }));
        console.log(allRequests);
        setRequests(allRequests);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };


    fetchWFHRequests();
  }, [user, userId]);

  // Update state when an action is successful (cancel/withdraw)
  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    // Determine the new status based on the action
    const updatedStatus = action === "cancel" ? ApprovalStatus.Cancelled : ApprovalStatus.PendingWithdrawal;

    // Update the requests state with the new status
    setRequests((prevRequests) =>
      prevRequests.map((request) =>
        request.arrangement_id === id
          ? { ...request, approval_status: updatedStatus } // Update the matching request
          : request // Keep other requests unchanged
      )
    );

    // Set a success message for the Snackbar
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

      {/* Pass requests and handleSuccess function to the child component */}
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
