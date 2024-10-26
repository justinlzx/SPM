import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/ApprovalStatus"; 
import { TWFHRequest } from "../team/PendingRequests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
        const allRequests: TWFHRequest[] = response.data.data.map(
          (request: any) => ({
            ...request,
            approval_status: ApprovalStatus[request.approval_status as keyof typeof ApprovalStatus],
            wfh_date: new Date(request.wfh_date).toISOString(),  
          })
        );
        console.log(allRequests);
        setRequests(allRequests);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };

    fetchRequests();
  }, [user, userId]);

  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    const updatedStatus =
      action === "cancel"
        ? ApprovalStatus.Cancelled
        : ApprovalStatus.PendingWithdrawal;

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
