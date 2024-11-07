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
import { capitalize } from "../../utils/utils";
import { ApprovalStatus } from "../../types/requests";
import { fetchEmployeeByStaffId } from "../../hooks/employee/employee.utils";
// import Filters from "../../common/Filters";
import { UserContext } from "../../context/UserContextProvider";
import axios from "axios";
import Filters, { TFilters } from "../../common/Filters";
import qs from "qs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type Arrangement = {
  arrangement_id: number;
  update_datetime: string;
  requester_staff_id: number;
  requester_name?: string;
  wfh_date: string;
  wfh_type: string;
  current_approval_status: ApprovalStatus;
  approving_officer: number;
  reason_description: string;
  requester_info: {
    staff_fname: string;
    staff_lname: string;
  };
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
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<"success" | "error">(
    "success"
  );

  const [filters, setFilters] = useState<TFilters>({
    startDate: null,
    endDate: null,
    workStatus: [],
    searchQuery: "",
  });

  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchAllRequests = async () => {
      if (user?.id) {
        try {
          setLoading(true);
          setError(null);

          const managerId = user.id;

          const arrangementsResponse = await axios.get(
            `${BACKEND_URL}/arrangements/team/${managerId}`,
            {
              withCredentials: true,
              headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
              },
              params: {
                current_approval_status: filters.workStatus,
                start_date: filters.startDate?.toISOString().split("T")[0],
                end_date: filters.endDate?.toISOString().split("T")[0],
                search_query: filters.searchQuery,
                items_per_page: rowsPerPage,
                page_num: page + 1,
              },
              paramsSerializer: (params) =>
                qs.stringify(params, { arrayFormat: "repeat" }),
            }
          );
          setTotalItems(arrangementsResponse.data.pagination_meta.total_count);
          const responseData = arrangementsResponse.data.data;

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
  }, [user, page, rowsPerPage, filters]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleSearchChange = (searchQuery: string) => {
    setSearchTerm(searchQuery);
  };

  const handleFilterChange = (filters: TFilters) => {
    setFilters(filters);
  };
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
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

  if (error) {
    return (
      <Typography color="error" align="center" sx={{ marginTop: 4 }}>
        {error}
      </Typography>
    );
  }

  return (
    <div data-cy="team-requests-filter">
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My Team's WFH/OOO Requests
      </Typography>

      <Filters
        onApplyFilters={(newFilters) => handleFilterChange(newFilters)}
        onClearFilters={(newFilters) => handleFilterChange(newFilters)}
        excludeStatusFilter={false}
        excludeSearchFilter={true}
      />

      <TableContainer
        component={Paper}
        sx={{
          marginTop: 3,
          maxHeight: "60vh", // Set a max height for the table container
          overflow: "auto", // Enable scroll within the table container if needed
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Staff Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody data-cy="arrangement-list">
            {arrangements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No arrangement data available
                </TableCell>
              </TableRow>
            ) : (
              arrangements.map((arrangement) => (
                <TableRow
                  key={arrangement.arrangement_id + arrangement.wfh_date}
                >
                  <TableCell>
                    {`${arrangement.requester_info.staff_fname} ${arrangement.requester_info.staff_lname}` ||
                      "N/A"}
                  </TableCell>
                  <TableCell>
                    {arrangement.wfh_type?.toUpperCase() || "N/A"}
                  </TableCell>
                  <TableCell>{arrangement.wfh_date || "N/A"}</TableCell>
                  <TableCell>
                    <Chip
                      label={capitalize(arrangement.current_approval_status)}
                      color={getChipColor(arrangement.current_approval_status)}
                    />
                  </TableCell>
                  <TableCell
                    style={{ whiteSpace: "normal", wordWrap: "break-word" }}
                  >
                    {arrangement.reason_description || "N/A"}
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
        count={totalItems}
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
