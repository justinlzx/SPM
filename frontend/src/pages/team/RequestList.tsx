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
  TextField,
  Chip,
  TablePagination,
  CircularProgress,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  wfh_date: string;
  wfh_type: string;
  approval_status: string;
  reason_description: string;
};

const getChipColor = (status: string) => {
  switch (status.toLowerCase()) {
    case "approved":
      return "success";
    case "pending":
      return "warning";
    case "rejected":
      return "error";
    default:
      return "default";
  }
};

export const RequestList = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchAllRequests = async () => {
      if (user?.id) {
        try {
          setLoading(true);
          setError(null);
          const response = await axios.get(
            `${BACKEND_URL}/arrangements/team/${user.id}`,
            {
              withCredentials: true, // Important for CORS
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              }
            }
          );
          const allRequests: TWFHRequest[] = response.data.data;
          setRequests(allRequests);
        } catch (error) {
          console.error("Failed to fetch all requests:", error);
          setError("Failed to fetch requests. Please try again later.");
        } finally {
          setLoading(false);
        }
      }
    };
    fetchAllRequests();
  }, [user]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setPage(0); // Reset to first page when searching
  };

  const filteredRequests = requests.filter(
    (request) =>
      request.reason_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.wfh_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      request.approval_status?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
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
      <Typography variant="h4" gutterBottom align="center" sx={{ marginTop: 4 }}>
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

      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center", width: "100%" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRequests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  {searchTerm ? "No matching requests found" : "No requests available"}
                </TableCell>
              </TableRow>
            ) : (
              filteredRequests
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((request) => (
                  <TableRow key={request.arrangement_id}>
                    <TableCell>
                      <Chip
                        color={getChipColor(request.approval_status)}
                        label={request.approval_status.charAt(0).toUpperCase() + request.approval_status.slice(1)}
                      />
                    </TableCell>
                    <TableCell>{request.wfh_type?.toUpperCase() || "N/A"}</TableCell>
                    <TableCell>{request.wfh_date || "N/A"}</TableCell>
                    <TableCell>{request.reason_description || "N/A"}</TableCell>
                  </TableRow>
                ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={filteredRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </div>
  );
};

