import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Container, Typography, Snackbar, Alert } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { WFHRequestTable } from "../../components/WFHRequestTable";
import { ApprovalStatus } from "../../types/status";
import { Filters } from "../../common/Filters";
import { TWFHRequest } from "../../types/requests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const MyWfhSchedulePage: React.FC = () => {
  const { user } = useContext(UserContext);
  const userId = user?.id;
  const navigate = useNavigate();

  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<TWFHRequest[]>([]);
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
        `${BACKEND_URL}/arrangements/personal/${userId}`
      );

      const allRequests: TWFHRequest[] = response.data.data.map(
        (request: any) => ({
          ...request,
        })
      );
      setRequests(allRequests);
      setFilteredRequests(allRequests); // Initialize filteredRequests with original data
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
  }, [user, userId]);

  const handleApplyFilters = (filters: {
    startDate: Date | null;
    endDate: Date | null;
    department: string[];
    status: ApprovalStatus[];
    searchQuery: string;
    workStatus: string[];
  }) => {
    const { startDate, endDate, department, status, searchQuery, workStatus } = filters;

    // Filter based on searchQuery and other filters
    const filtered = requests.filter((request) => {
      const matchesDate =
        (!startDate || new Date(request.wfh_date) >= startDate) &&
        (!endDate || new Date(request.wfh_date) <= endDate);

      const matchesStatus =
        status.length === 0 || status.includes(request.current_approval_status);

      // const matchesDepartment =
      //   department.length === 0 || department.includes(request.department); // Assuming department is a field

      const matchesWorkStatus =
        workStatus.length === 0 || workStatus.includes(request.wfh_type);

      const matchesSearchQuery =
        !searchQuery ||
        request.requester_staff_id.toString().includes(searchQuery) ||
        request.wfh_date.includes(searchQuery) ||
        request.reason_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.wfh_type.toLowerCase().includes(searchQuery.toLowerCase());

      return (
        matchesDate &&
        matchesStatus &&
        //matchesDepartment &&
        matchesWorkStatus &&
        matchesSearchQuery
      );
    });

    setFilteredRequests(filtered);
  };

  const handleClearFilters = () => {
    fetchRequests(); // Refetch the original data and reset filters
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
  };

  const handleCloseSnackBar = () => setOpenSnackbar(false);

  return (
    <Container sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My WFH Request Overview
      </Typography>
      <Filters
        onApplyFilters={handleApplyFilters}
        onClearFilters={handleClearFilters}
      />
      <WFHRequestTable requests={filteredRequests} handleSuccess={handleSuccess} />
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
