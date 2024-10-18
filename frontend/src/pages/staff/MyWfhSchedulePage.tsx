import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  staff_id: number;
  wfh_date: string; 
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  approval_status: string;
};


export const MyWfhSchedulePage: React.FC = () => {
  const [wfhRequests, setWfhRequests] = useState<TWFHRequest[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");

  const { user } = useContext(UserContext);
  const storedUser = localStorage.getItem("user")?.toLowerCase();

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

  useEffect(() => {
    const fetchWFHRequests = async () => {
      if (!user || userId === null) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );
        setWfhRequests(response.data.data);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };


    fetchWFHRequests();
  }, [user, userId]);

  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    const updatedStatus = action === "cancel" ? "cancelled" : "withdrawn";

    setWfhRequests((prevRequests) =>
      prevRequests.map((request) =>
        request.arrangement_id === id
          ? { ...request, approval_status: updatedStatus }
          : request
      )
    );

    const message =
      action === "cancel"
        ? "Your request has been successfully cancelled!"
        : "Your request has been successfully withdrawn!";
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
        requests={wfhRequests}
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
