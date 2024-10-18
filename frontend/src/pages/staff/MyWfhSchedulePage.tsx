import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/ApprovalStatus";  

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  staff_id: number;
  wfh_date: string; 
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  approval_status: ApprovalStatus;
};

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

export const MyWfhSchedulePage: React.FC = () => {
  const [wfhRequests, setWfhRequests] = useState<TWFHRequest[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");

  const { user } = useContext(UserContext);
  const storedUser = localStorage.getItem("user")?.toLowerCase();

  // Fetch user ID based on stored email
  useEffect(() => {
    const fetchUserId = async () => {
      if (storedUser) {
        try {
          const response = await axios.get(
            `${BACKEND_URL}/employees/email/${storedUser}`
          );
          setUserId(response.data.staff_id);
          localStorage.setItem("id", response.data.staff_id);
        } catch (error) {
          console.error("Failed to fetch user ID:", error);
        }
      }
    };
    fetchUserId();
  }, [storedUser]);

  // Fetch WFH requests for the user
  useEffect(() => {
    const fetchWFHRequests = async () => {
      if (!user || userId === null) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );
        
        const fetchedRequests = response.data.data.map((request: any) => ({
          ...request,
          approval_status: mapApprovalStatus(request.approval_status), 
        }));

        setRequests(fetchedRequests);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };


    fetchWFHRequests();
  }, [user, userId]);

  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    const updatedStatus = action === "cancel" ? ApprovalStatus.Cancelled : ApprovalStatus.PendingWithdrawal;

    setWfhRequests((prevRequests) =>
      prevRequests.map((request) =>
        request.arrangement_id === id
          ? { ...request, approval_status: updatedStatus }
          : request
      )
    );

    const message =
      action === "cancel"
        ? "Your WFH request has been successfully cancelled!"
        : "Withdrawal Request has been sent to your manager for review.";
    setSnackbarMessage(message);
    setOpenSnackbar(true);
  };

  const handleCloseSnackBar = (
    event?: React.SyntheticEvent | Event,
    reason?: string
  ) => {
    if (reason === "clickaway") return;
    setOpenSnackbar(false);
  };

  return (
    <Container sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My WFH Request Overview
      </Typography>

      <WFHRequestTable
        requests={requests} 
        handleSuccess={(id: number, action: "cancel" | "withdraw") =>
          handleSuccess(id, action)
        }
      />

      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 8 }}>
        My OOO Request Overview
      </Typography>

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
