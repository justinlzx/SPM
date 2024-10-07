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
  Typography,
  Box,
  Button,
  TextField,
  InputAdornment,
  Chip,
  ChipProps,
  TablePagination,
} from "@mui/material";
import SearchIcon from '@mui/icons-material/Search';
import { Filters } from "../../components/Filters";
import { UserContext } from "../../context/UserContextProvider";
import { TRequest } from "../../hooks/auth/arrangement/arrangement.utils";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import { capitalize } from "../../utils/utils";
import { Filter } from "@mui/icons-material";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type TOrder = "asc" | "desc";

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
  approval_status: ApprovalStatus;
};

// Type for the filter values
type FilterValues = {
  startDate: Date | null;
  endDate: Date | null;
  wfhType: string;
  requestStatus: string[];
  departments: string[];
  workType: string;
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

export const WfhSchedulePage = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [order, setOrder] = useState<TOrder>("asc");
  const [orderBy, setOrderBy] = useState<keyof TWFHRequest | "staff_id">("staff_id");
  const [filters, setFilters] = useState<FilterValues | {}>({});
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [userId, setUserId] = useState<number | null>(null);

  const { user } = useContext(UserContext);

  // Retrieve user's email from local storage
  const storedUser = localStorage.getItem("user");

  useEffect(() => {
    const fetchUserId = async () => {
      if (storedUser) {
        try {
            const response = await axios.get(`${BACKEND_URL}/employee/email/${storedUser}`, {
            });
          setUserId(response.data.staff_id);
          localStorage.setItem("id", response.data.staff_id);
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
        const response = await axios.get(`${BACKEND_URL}/arrangement/view/all-requests/${storedId}`);
        const allRequests: TWFHRequest[] = response.data.data;
        setRequests(allRequests);
      } catch (error) {
        console.error("Failed to fetch requests:", error);
      }
    };
    fetchRequests();
  }, [user, userId]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Add explicit type for selectedFilters
  const handleApplyFilters = (selectedFilters: FilterValues) => {
    setFilters(selectedFilters);
    console.log("Applied Filters:", selectedFilters);
  };

  return (
    <Container>
      <Typography
        variant="h4"
        gutterBottom
        align="left"
        sx={{ marginTop: 4 }}
      >
        My WFH Request Overview
      </Typography>

      {/* Search bar */}
      <TextField
        label="Search"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
        InputProps={{
          endAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />
      <Filters onApply={handleApplyFilters} />

      <TableContainer
        component={Paper}
        sx={{ marginTop: 3, textAlign: "center" }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Date Submitted</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">No requests found</TableCell>
              </TableRow>) : (
              requests
                .filter((request) =>
                  Object.values(request)
                    .some(value => value.toString().toLowerCase().includes(searchTerm.toLowerCase()))
                )
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((request) => {
                  const {
                    arrangement_id,
                    wfh_date,
                    wfh_type,
                    approval_status,
                  } = request;

                  return (
                    <TableRow key={arrangement_id}>
                      <TableCell>{wfh_date}</TableCell>
                      <TableCell>{capitalize(wfh_type)}</TableCell>
                      <TableCell>-</TableCell> {/* Placeholder for 'Reason' */}
                      <TableCell>{wfh_date}</TableCell> {/* Placeholder for 'Date Submitted' */}
                      <TableCell>
                        <Chip
                          color={getChipColor(approval_status as ApprovalStatus)}
                          label={capitalize(approval_status)}
                        />
                      </TableCell>
                      <TableCell>
                        {approval_status === ApprovalStatus.Rejected && (
                          <Button
                            size="small"
                            color="error"
                            variant="outlined"
                          >
                            View Reason
                          </Button>
                        )}
                        {approval_status === ApprovalStatus.Pending && (
                          <Button
                            size="small"
                            variant="contained"
                            disabled
                          >
                            Withdraw
                          </Button>
                        )}
                        {approval_status === ApprovalStatus.Approved && (
                          <Button
                            size="small"
                            variant="outlined"
                            color="primary"
                          >
                            Cancel
                          </Button>
                        )}
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

export default WfhSchedulePage;
