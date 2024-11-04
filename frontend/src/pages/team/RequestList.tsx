import React, { useState, useEffect, useContext } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Chip,
  TextField,
  TablePagination,
  Snackbar,
  Alert,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type Arrangement = {
  arrangement_id: number;
  update_datetime: string;
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  current_approval_status: string;
  approving_officer: number;
  reason_description: string;
};

const getChipColor = (status: string | undefined) => {
  if (!status) return "default";
  switch (status.toLowerCase()) {
    case "approved":
      return "success";
    case "pending approval":
      return "warning";
    case "rejected":
      return "error";
    default:
      return "default";
  }
};

export const RequestList = () => {
  const [arrangements, setArrangements] = useState<Arrangement[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<"success" | "error">("success");
  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchAllRequests = async () => {
      if (user?.id) {
        try {
          setLoading(true);
          setError(null);

          const managerResponse = await axios.get(
            `${BACKEND_URL}/employees/manager/peermanager/${user.id}`,
            {
              withCredentials: true,
              headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
              },
            }
          );

          const managerId = managerResponse.data.manager_id;
          if (!managerId) {
            throw new Error("Manager ID not found");
          }

          const arrangementsResponse = await axios.get(
            `${BACKEND_URL}/arrangements/team/${managerId}`,
            {
              withCredentials: true,
              headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
              },
            }
          );

          const responseData = arrangementsResponse.data.data.flatMap(
            (item: any) => item.pending_arrangements
          );
          setArrangements(responseData);
        } catch (error) {
          console.error("Failed to fetch data:", error);
          setError("Failed to fetch team requests. Please try again later.");
        } finally {
          setLoading(false);
        }
      }
    };

    fetchAllRequests();
  }, [user]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
  };

  const filteredArrangements = arrangements.filter(
    (arrangement) =>
      arrangement.reason_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      arrangement.wfh_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      arrangement.current_approval_status?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
        <CircularProgress />
      </div>
    );
  }

  if (error) {
    return (
      <Typography color="error" align="center" sx={{ marginTop: 4 }}>
        {error}
      </Typography>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My Team's WFH/OOO Requests
      </Typography>

      <TextField
        label="Search by reason, type or status"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      />

      <TableContainer
        component={Paper}
        sx={{
          marginTop: 3,
          maxHeight: "60vh", // Set a max height for the table container
          overflow: "auto", // Enable scroll within the table container if needed
        }}
      >
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Arrangement ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Approving Officer</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredArrangements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No arrangement data available
                </TableCell>
              </TableRow>
            ) : (
              filteredArrangements
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((arrangement) => (
                  <TableRow key={arrangement.arrangement_id}>
                    <TableCell>{arrangement.arrangement_id}</TableCell>
                    <TableCell>{arrangement.approving_officer || "N/A"}</TableCell>
                    <TableCell>{arrangement.wfh_type?.toUpperCase() || "N/A"}</TableCell>
                    <TableCell>{arrangement.wfh_date || "N/A"}</TableCell>
                    <TableCell>
                      <Chip
                        label={arrangement.current_approval_status}
                        color={getChipColor(arrangement.current_approval_status)}
                      />
                    </TableCell>
                    <TableCell>{arrangement.reason_description || "N/A"}</TableCell>
                  </TableRow>
                ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={filteredArrangements.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      <Snackbar
        open={showSnackbar}
        onClose={handleCloseSnackBar}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
        autoHideDuration={6000}
      >
        <Alert onClose={handleCloseSnackBar} severity={alertStatus}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </div>
  );
};