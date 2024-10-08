import React, { useEffect, useState, useContext } from "react";
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
  Chip,
  ChipProps,
  TablePagination,
} from "@mui/material";
import { capitalize } from "../../utils/utils";
import { UserContext } from '../../context/UserContextProvider';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
enum ApprovalStatus {
  Approved = "approved",
  Pending = "pending",
  Rejected = "rejected",
}

enum WfhType {
  AM = "AM",
  PM = "PM",
  FULL = "FULL",
}

type TWFHRequest = {
  requester_staff_id?: number;
  wfh_date?: string;
  wfh_type?: WfhType;
  arrangement_id?: number;
  approval_status?: ApprovalStatus;
  reason_description?: string;
};

const getChipColor = (status: ApprovalStatus | undefined): ChipProps["color"] => {
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.Pending:
      return "warning";
    case ApprovalStatus.Rejected:
      return "error";
    default:
      return "default";
  }
};

const getWfhTypeChipColor = (wfhType: WfhType | undefined): ChipProps["color"] => {
  switch (wfhType) {
    case WfhType.AM:
      return "primary";
    case WfhType.PM:
      return "info";
    case WfhType.FULL:
      return "secondary";
    default:
      return "default";
  }
};

export const RequestList = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Retrieve user information from context
  const { user } = useContext(UserContext);

  // Fetch all requests from the backend
  useEffect(() => {
    const fetchAllRequests = async () => {
      try {
        if (user) {
          const response = await axios.get(`${BACKEND_URL}/arrangements/personal/${user.id}`);
          const userRequests: TWFHRequest[] = response.data.data;

          // Filter requests to only include those submitted by the logged-in user
          setRequests(userRequests);
        }
      } catch (error) {
        console.error("Failed to fetch all requests:", error);
      }
    };
    fetchAllRequests();
  }, [user]);

  // Handle search input
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Handle change in page number
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle change in rows per page
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Filter the requests based on the search term, with null checks
  const filteredRequests = requests.filter(
    (request) =>
      (request.requester_staff_id && request.requester_staff_id.toString().includes(searchTerm)) ||
      (request.wfh_date && request.wfh_date.includes(searchTerm)) ||
      (request.wfh_type && request.wfh_type.toLowerCase().includes(searchTerm)) ||
      (request.approval_status && request.approval_status.toLowerCase().includes(searchTerm)) ||
      (request.reason_description && request.reason_description.toLowerCase().includes(searchTerm))
  );

  return (
    <div>
      {/* <Typography variant="h4" gutterBottom align="center" sx={{ marginTop: 4 }}>
        Your WFH Requests
      </Typography> */}
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
                  No requests found
                </TableCell>
              </TableRow>
            ) : (
              filteredRequests
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((request) => {
                  const { arrangement_id, wfh_date, wfh_type, approval_status, reason_description } = request;

                  return (
                    <TableRow key={arrangement_id} sx={{ alignItems: "center" }}>
                      <TableCell
                        sx={{
                          width: { xs: "30%", sm: "20%", md: "15%", lg: "15%" },
                          padding: "15px",
                        }}
                      >
                        <Chip
                          color={getChipColor(approval_status)}
                          label={capitalize(approval_status || "N/A")}
                          sx={{ margin: "0" }}
                        />
                      </TableCell>

                      <TableCell
                        sx={{ width: { xs: "30%", sm: "20%", md: "15%", lg: "15%" }, padding: "10px" }}
                      >
                        <Chip
                          color={getWfhTypeChipColor(wfh_type)}
                          label={wfh_type ? wfh_type.toUpperCase() : "N/A"}
                          sx={{ margin: "0" }}
                        />
                      </TableCell>
                      <TableCell>{wfh_date || "N/A"}</TableCell>
                      <TableCell>{reason_description ? reason_description.substring(0, 15) : "N/A"}</TableCell>
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
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </div>
  );
};

export default RequestList;
