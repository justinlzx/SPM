import { useContext, useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/status";
import { Filters, TFilters } from "../../common/Filters";
import { TWFHRequest } from "../../types/requests";
import qs from "qs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const MyWfhSchedulePage = () => {
  const { user } = useContext(UserContext);
  const userId = user?.id;
  const navigate = useNavigate();

  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilters>({
    startDate: null,
    endDate: null,
    workStatus: [],
    searchQuery: "",
  });
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarSeverity, setSnackbarSeverity] = useState<"success" | "error">(
    "success"
  );

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  const fetchRequests = async () => {
    if (!user || !userId) return;

    try {
      const response = await axios.get(
        `${BACKEND_URL}/arrangements/personal/${userId}`,
        {
          params: {
            current_approval_status: filters.workStatus || [],
            start_date: filters.startDate?.toISOString().split("T")[0],
            end_date: filters.endDate?.toISOString().split("T")[0],
          },
          paramsSerializer: (params) =>
            qs.stringify(params, { arrayFormat: "repeat" }),
        }
      );

      const allRequests: TWFHRequest[] = response.data.data.map(
        (request: any) => ({
          ...request,
        })
      );
      setRequests(allRequests);
    } catch (error) {
      console.error("Failed to fetch WFH requests:", error);
      setSnackbarMessage(
        "Failed to fetch WFH requests. Please try again later."
      );
      setSnackbarSeverity("error");
      setOpenSnackbar(true);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [user, userId, filters]);

  const handleApplyFilters = (filters: TFilters) => {
    setFilters(filters);
  };

  const handleClearFilters = (filters: TFilters) => {
    setFilters({
      startDate: null,
      endDate: null,
      workStatus: [],
      searchQuery: "",
    });
  };

  const handleSuccess = (id: number, action: "cancel" | "withdraw") => {
    const updatedStatus =
      action === "cancel"
        ? ApprovalStatus.Cancelled
        : ApprovalStatus.PendingWithdrawal;

    setRequests((prevRequests) =>
      prevRequests.map((request) =>
        request.arrangement_id === id
          ? { ...request, current_approval_status: updatedStatus }
          : request
      )
    );

    setSnackbarMessage(
      action === "cancel"
        ? "Your WFH request has been successfully cancelled!"
        : "Withdrawal Request has been sent to your manager for review."
    );
    setSnackbarSeverity("success");
    setOpenSnackbar(true);
    fetchRequests();
  };

  const handleCloseSnackBar = () => setOpenSnackbar(false);

  return (
    <Container sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My WFH Request Overview
      </Typography>
      <Filters
        onApplyFilters={(filters) => handleApplyFilters(filters)}
        onClearFilters={(filters) => handleClearFilters(filters)}
      />
      <WFHRequestTable
        requests={requests}
        handleSuccess={handleSuccess}
        refreshData={fetchRequests}
      />
      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackBar}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert onClose={handleCloseSnackBar} severity={snackbarSeverity}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default MyWfhSchedulePage;
