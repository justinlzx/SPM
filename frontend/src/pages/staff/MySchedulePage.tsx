import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { OOORequestTable } from "../../components/OOORequestTable";

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

type TOOORequest = {
  arrangement_id: number;
  staff_id: number;
  ooo_start_date: string;
  ooo_end_date?: string;
  reason_description: string;
  approval_status: string;
};

export const MySchedulePage: React.FC = () => {
  const [wfhRequests, setWfhRequests] = useState<TWFHRequest[]>([]);
  const [oooRequests, setOooRequests] = useState<TOOORequest[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");

  const { user } = useContext(UserContext);
  const storedUser = localStorage.getItem("user");

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

    const fetchOOORequests = async () => {
      if (!user || userId === null) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/ooo/${userId}`
        );
        setOooRequests(response.data.data);
      } catch (error) {
        console.error("Failed to fetch OOO requests:", error);
      }
    };

    fetchWFHRequests();
    fetchOOORequests();
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

    setOooRequests((prevRequests) =>
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

      <OOORequestTable
        requests={oooRequests}
        handleSuccess={(id: number, action: "cancel" | "withdraw") =>
          handleSuccess(id, action)
        }
      />

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

export default MySchedulePage;
