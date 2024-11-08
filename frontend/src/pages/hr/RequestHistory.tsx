import React, { useContext, useEffect, useState } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { useNavigate } from "react-router-dom";
import {
  Container,
  Typography,
  Divider,
  Snackbar,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  Chip,
  TablePagination,
  CircularProgress,
} from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  action: string;
  approving_officer: number;
  arrangement_id: number;
  batch_id: number | null;
  log_id: number;
  previous_approval_status: string | null;
  reason_description: string;
  requester_staff_id: number;
  status_reason: string | null;
  supporting_doc_1: string | null;
  supporting_doc_2: string | null;
  supporting_doc_3: string | null;
  update_datetime: string;
  updated_approval_status: string;
  wfh_date: string;
  wfh_type: string;
};

const getChipColor = (status: string | undefined) => {
  if (!status) return "default"; // Default if status is undefined
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

export const RequestHistoryPage: React.FC = () => {
  const { user } = useContext(UserContext);
  const [logs, setLogs] = useState<TWFHRequest[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<"success" | "error">(
    "success"
  );
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    fetchLogs();
  }, [user, navigate]);

  const handleCloseSnackBar = () => setShowSnackbar(false);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/arrangements/logs/all`);
      const fetchedLogs = response.data.data; 
      console.log(response.data);
      setLogs(fetchedLogs);
    } catch (error) {
      console.error("Error fetching arrangement logs:", error);
      setAlertStatus("error");
      setSnackbarMessage("Failed to load Request History.");
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setPage(0); 
  };

  const filteredLogs = logs.filter(
    (log) =>
      log.reason_description
        ?.toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      log.wfh_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.updated_approval_status
        ?.toLowerCase()
        .includes(searchTerm.toLowerCase()) || 
      log.approving_officer
        .toString()
        .includes(searchTerm) || 
      log.requester_staff_id
        .toString()
        .includes(searchTerm)
  );
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (loading) {
    return (
      <div
        style={{ display: "flex", justifyContent: "center", padding: "2rem" }}
      >
        <CircularProgress />
      </div>
    );
  }

  return (
    <Container>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        WFH Request History
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <TextField
        label="Search by reason, type, or status"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      />

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                Approving Officer ID
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Requester ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Update Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  {searchTerm
                    ? "No matching requests found"
                    : "No requests available"}
                </TableCell>
              </TableRow>
            ) : (
              filteredLogs
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((log) => (
                  <TableRow key={log.arrangement_id}>
                    <TableCell>
                      <Chip
                        color={getChipColor(log.updated_approval_status)}
                        label={
                          log.updated_approval_status.charAt(0).toUpperCase() +
                          log.updated_approval_status.slice(1)
                        }
                      />
                    </TableCell>
                    <TableCell>{log.approving_officer || "N/A"}</TableCell>
                    <TableCell>{log.requester_staff_id || "N/A"}</TableCell>
                    <TableCell>
                      {log.wfh_type?.toUpperCase() || "N/A"}
                    </TableCell>
                    <TableCell>
                      {new Date(log.wfh_date).toLocaleDateString() || "N/A"}
                    </TableCell>
                    <TableCell>{log.reason_description || "N/A"}</TableCell>
                    <TableCell>{log.action || "N/A"}</TableCell>
                    <TableCell>
                      {new Date(log.update_datetime).toLocaleString() || "N/A"}
                    </TableCell>
                  </TableRow>
                ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={filteredLogs.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      {/* Snackbar for alerts */}
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
    </Container>
  );
};

export default RequestHistoryPage;
