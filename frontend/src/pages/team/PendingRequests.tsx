import React, { useContext, useEffect, useState } from "react";
import axios from 'axios';
import {
  Container,
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
  ChipProps,
  Button,
  ButtonGroup,
  TablePagination,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { capitalize } from "../../utils/utils";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import qs from 'qs';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
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
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { user } = useContext(UserContext);
  const [userId, setUserId] = useState<number | null>(null);
  const storedUser = localStorage.getItem("user");

  useEffect(() => {
    const fetchUserId = async () => {
      if (storedUser) {
        try {
          const response = await axios.get(`${BACKEND_URL}/employees/email/${storedUser}`); // Call your /email endpoint
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
      if (!user || !storedId) return;
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view/pending-requests/${storedId}`);
        const allRequests: TWFHRequest[] = response.data.data;

        // Filter for pending requests, excluding Jack Sim's approved requests
        const filteredRequests = allRequests.filter((request: TWFHRequest) => {
          if (request.staff_id === 130002 && request.approval_status === ApprovalStatus.Approved) {
            return false;
          }
          return request.approval_status === ApprovalStatus.Pending;
        });

        setRequests(filteredRequests);
      } catch (error) {
        console.error("Failed to fetch requests:", error);
      }
    };
    fetchRequests();
  }, [user, storedId]);

  const handleRequestAction = async (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => {
    try {
      const formData = new FormData();
      formData.append('action', action);
      formData.append('reason_description', reason_description);
      formData.append('approving_officer', userId?.toString() || '');
  
      // Log the payload before sending it
      console.log('Payload being sent:', {
        reason_description: reason_description,
        action: action,
        approving_officer: userId,
      });
  
      await axios.put(`${BACKEND_URL}/arrangements/${arrangement_id}/status`, formData, {
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

  const filteredRequests = requests.filter(
    (request) =>
      request.staff_id.toString().includes(searchTerm) ||
      request.wfh_date.includes(searchTerm) ||
      request.wfh_type.toLowerCase().includes(searchTerm) ||
      request.approval_status.toLowerCase().includes(searchTerm)
  );

  return (
    <Container>
      {/* <Typography variant="h4" gutterBottom align="center" sx={{ marginTop: 4 }}>
        Pending Requests for {userName}
      </Typography> */}
      <TextField
        label="Search"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      />
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Requester Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell> {/* New Column */}
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRequests.length === 0 ? (
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
                      <Chip color={getChipColor(approval_status)} label={capitalize(approval_status)} />
                    </TableCell>
                    <TableCell>
                      <ButtonGroup variant="contained" aria-label="Approve/Reject Button group">
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
        count={filteredRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) => setRowsPerPage(parseInt(event.target.value, 10))}
      />
    </Container>
  );
};
