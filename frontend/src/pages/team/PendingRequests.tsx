import React, { useContext, useEffect, useState } from "react";
import axios from 'axios'; // Import axios
import {
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TableSortLabel,
  Typography,
  Box,
  TextField,
  Chip,
  ChipProps,
  Button,
  ButtonGroup,
  TablePagination,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { TRequest } from "../../hooks/auth/arrangement/arrangement.utils";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import { capitalize } from "../../utils/utils";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type TOrder = "asc" | "desc";
type TAction = "approve" | "reject";

enum ApprovalStatus {
  Approved = "approved",
  Pending = "pending",
  Rejected = "rejected",
}

type TWFHRequest = {
  staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  reason_description: string; // Include reason_description here
  approval_status: ApprovalStatus;
};

const getChipColor = (status: ApprovalStatus): ChipProps["color"] => {
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.Pending:
      return "warning";
    case ApprovalStatus.Rejected:
      return "error";
    default:
      return "default"; // Fallback if needed
  }
};

export const PendingRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [order, setOrder] = useState<TOrder>("asc");
  const [orderBy, setOrderBy] = useState<keyof TWFHRequest | "staff_id">("staff_id");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [userId, setUserId] = useState<number | null>(null); // State to hold staff ID

  const { user } = useContext(UserContext);

  // Retrieve user's email from local storage
  const storedUser = localStorage.getItem("user");

  useEffect(() => {
    const fetchUserId = async () => {
      if (storedUser) {
        try {
          const response = await axios.get(`${BACKEND_URL}/employee/email?email=${storedUser}`);
          setUserId(response.data.staff_id); // Set the staff ID in state
          localStorage.setItem("id", response.data.staff_id)
        } catch (error) {
          console.error("Failed to fetch user ID:", error);
        }
      }
    };

    fetchUserId();
  }, [storedUser]);

  // Retrieve user's id from local storage
  const storedId = localStorage.getItem("id");

  useEffect(() => {
    const fetchRequests = async () => {
      if (!user || userId === null) return; // Ensure userId is available
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view/pending-requests/${storedId}`); // Call your /view endpoint
        const allRequests: TWFHRequest[] = response.data.data; // Adjust according to your response structure
        const filteredRequests = allRequests.filter((request: TWFHRequest) => request.approval_status === ApprovalStatus.Pending); // Filter for pending requests
        setRequests(filteredRequests);
      } catch (error) {
        console.error("Failed to fetch requests:", error);
      }
    };
    fetchRequests();
  }, [user, userId]); // Removed page and rowsPerPage as dependencies for fetching all requests

  const handleRequestAction = async (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => {
    try {
      const formData = new FormData();
      formData.append('arrangement_id', arrangement_id.toString());
      formData.append('reason', reason_description);
  
      // Log the payload before sending it
      console.log('Payload being sent:', {
        arrangement_id: arrangement_id,
        reason: reason_description,
      });
  
      await axios.post(`${BACKEND_URL}/arrangement/request/${action}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
  
      console.log(`Request ${action}d successfully`);
    } catch (error) {
      console.error(`Error ${action}ing request:`, error);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Container>
      <Typography
        variant="h4"
        gutterBottom
        align="center"
        sx={{ marginTop: 4 }}
      >
        Pending Requests for {storedUser} (Staff ID: {userId})
      </Typography>

      {/* Search bar */}
      <TextField
        label="Search"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      />

      <TableContainer
        component={Paper}
        sx={{ marginTop: 3, textAlign: "center" }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "staff_id"}
                  direction={orderBy === "staff_id" ? order : "asc"}
                >
                  Requester Staff ID
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell> {/* New Column */}
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">No pending requests</TableCell>
              </TableRow>
            ) : (
              requests.map((request) => {
                const {
                  arrangement_id,
                  wfh_date,
                  wfh_type,
                  approval_status,
                  reason_description, // Ensure this is included
                  staff_id,
                } = request; // Access properties directly

                return (
                  <TableRow key={arrangement_id}>
                    <TableCell>{staff_id}</TableCell>
                    <TableCell>{wfh_date}</TableCell>
                    <TableCell>{wfh_type?.toUpperCase()}</TableCell>
                    <TableCell>{reason_description}</TableCell> {/* Display Reason Description */}
                    <TableCell>
                      <Chip
                        color={getChipColor(approval_status as ApprovalStatus)}
                        label={capitalize(approval_status!)}
                      />
                    </TableCell>
                    <TableCell>
                      <ButtonGroup
                        variant="contained"
                        aria-label="Approve/Reject Button group"
                      >
                        <Button
                          size="small"
                          color="success"
                          startIcon={<CheckIcon />}
                          onClick={() =>
                            handleRequestAction("approve", arrangement_id!, reason_description!)
                          }
                        >
                          Approve
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<CloseIcon />}
                          onClick={() =>
                            handleRequestAction("reject", arrangement_id!, reason_description!)
                          }
                        >
                          Reject
                        </Button>
                      </ButtonGroup>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={requests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Container>
  );
};
