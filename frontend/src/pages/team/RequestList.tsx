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
import { ApprovalStatus } from "../../types/requests";
import Filters from "../../common/Filters";
import { UserContext } from "../../context/UserContextProvider";
import axios from "axios";
import qs from "qs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type Arrangement = {
  arrangement_id: number;
  update_datetime: string;
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  current_approval_status: ApprovalStatus;
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
  const [filteredArrangements, setFilteredArrangements] = useState<
    Arrangement[]
  >([]);
  const [baseArrangements, setBaseArrangements] = useState<Arrangement[]>([]);
  const [arrangements, setArrangements] = useState<Arrangement[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<"success" | "error">(
    "success"
  );
  const { user } = useContext(UserContext);

  useEffect(() => {
    fetchAllRequests();
  }, [user]);

  const fetchAllRequests = async (
    startDate: Date | null = null,
    endDate: Date | null = null,
    status: ApprovalStatus[] = [],
    department: string[] = []
  ) => {
    if (user?.id) {
      try {
        setLoading(true);
        setError(null);

        const instance = axios.create({
          withCredentials: true,
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          paramsSerializer: (params: Record<string, any>): string => {
            const serializedParams: Record<string, any> = {};

            Object.entries(params).forEach(([key, value]) => {
              // Only serialize non-null values
              if (value !== null && value !== undefined) {
                if (value instanceof Date) {
                  serializedParams[key] = value.toISOString().split("T")[0]; // Format date as YYYY-MM-DD
                } else if (
                  Array.isArray(value) &&
                  (key === "current_approval_status" || key === "department")
                ) {
                  serializedParams[key] = value;
                } else {
                  serializedParams[key] = value;
                }
              }
            });

            return qs.stringify(serializedParams, { arrayFormat: "repeat" });
          },
        });

        const arrangementsResponse = await instance.get(
          `${BACKEND_URL}/arrangements/team/${user.id}`,
          {
            params: {
              start_date: startDate,
              end_date: endDate,
              current_approval_status: status,
              department: department,
            },
          }
        );

        const responseData = arrangementsResponse.data.data;
        console.log(responseData);
        if (baseArrangements.length === 0) {
          console.log("Setting base arrangements");
          setBaseArrangements(responseData);
          setArrangements(responseData);
        } else {
          setFilteredArrangements(responseData);
          setArrangements(responseData);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
        setError("Failed to fetch team requests. Please try again later.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleSearchChange = (searchQuery: string) => {
    setSearchTerm(searchQuery);
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
  // const filteredArrangements = arrangements.filter(
  //   (arrangement) =>
  //     arrangement.reason_description
  //       ?.toLowerCase()
  //       .includes(searchTerm.toLowerCase()) ||
  //     arrangement.wfh_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
  //     arrangement.current_approval_status
  //       ?.toLowerCase()
  //       .includes(searchTerm.toLowerCase())
  // );

  const onApplyFilters = (filters: {
    startDate: Date | null;
    endDate: Date | null;
    department: string[];
    status: ApprovalStatus[];
    searchQuery: string;
    workStatus: string[];
  }) => {
    if (
      !filters.startDate ||
      !filters.endDate ||
      !filters.department ||
      !filters.status
    ) {
      fetchAllRequests(
        filters.startDate,
        filters.endDate,
        filters.status,
        filters.department
      );
    }

    const filtered = arrangements.filter((request) => {
      // const matchesDate =
      //   (!filters.startDate ||
      //     new Date(request.wfh_date) >= filters.startDate) &&
      //   (!filters.endDate || new Date(request.wfh_date) <= filters.endDate);

      // const matchesStatus =
      //   filters.status.length === 0 ||
      //   filters.status.includes(request.current_approval_status);

      const searchQuery = filters.searchQuery.toLowerCase();
      const matchesSearchQuery =
        !searchQuery ||
        request.reason_description.toLowerCase().includes(searchQuery) ||
        request.wfh_type.toLowerCase().includes(searchQuery) ||
        request.wfh_date.includes(searchQuery) ||
        request.requester_staff_id.toString().includes(searchQuery);

      return matchesSearchQuery;
    });
    setFilteredArrangements(filtered);
  };

  const onClearFilters = () => {
    console.log("Clearing filters");
    setArrangements(baseArrangements);
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
    <div>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        My Team's WFH/OOO Requests
      </Typography>

      {/* <TextField
        label="Search by reason, type or status"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      /> */}

      <Filters
        onApplyFilters={onApplyFilters}
        onClearFilters={onClearFilters}
        experimentalFlag={true}
        onSearchChange={handleSearchChange}
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
              <TableCell sx={{ fontWeight: "bold" }}>
                Approving Officer
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {arrangements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No arrangement data available
                </TableCell>
              </TableRow>
            ) : (
              arrangements
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((arrangement) => (
                  <TableRow key={arrangement.arrangement_id}>
                    <TableCell>{arrangement.arrangement_id}</TableCell>
                    <TableCell>
                      {arrangement.approving_officer || "N/A"}
                    </TableCell>
                    <TableCell>
                      {arrangement.wfh_type?.toUpperCase() || "N/A"}
                    </TableCell>
                    <TableCell>{arrangement.wfh_date || "N/A"}</TableCell>
                    <TableCell>
                      <Chip
                        label={arrangement.current_approval_status}
                        color={getChipColor(
                          arrangement.current_approval_status
                        )}
                      />
                    </TableCell>
                    <TableCell>
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
        count={arrangements.length}
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
