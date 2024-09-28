import React, { useContext, useEffect, useState } from "react";
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
} from "@mui/material";
import { useArrangement } from "../../hooks/auth/arrangements/arrangement";
import { UserContext } from "../../context/UserContextProvider";
import { Request } from "../../hooks/auth/arrangements/arrangement.utils";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import { capitalize } from "../../utils/utils";

// Define types

type Employee = {
  staff_id: number;
  staff_fname: string;
  staff_lname: string;
  position: string;
  country: string;
  email: string;
  dept: string;
};

type Order = "asc" | "desc";

enum ApprovalStatus {
  Approved = "approved",
  Pending = "pending",
  Rejected = "rejected",
}

// This function maps ApprovalStatus to Chip color values
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
  const [requests, setRequests] = useState<Request[]>([]);
  const [employees, setEmployees] = useState<{ [key: number]: Employee }>({});
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState<Order>("asc");
  const [orderBy, setOrderBy] = useState<
    keyof Request | keyof Employee | "full_name"
  >("requester_staff_id"); // Default sorting by staff ID
  const [searchTerm, setSearchTerm] = useState(""); // New state for search term

  const { mutateAsync: arrangementMutation, isPending } = useArrangement();
  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchRequests = async () => {
      if (!user) return;
      const result = await arrangementMutation({
        id: user.id,
        status: "pending",
      });
      setRequests(result!);
    };
    fetchRequests();
  }, [setRequests, arrangementMutation, user]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  return (
    <Container>
      <Typography
        variant="h4"
        gutterBottom
        align="center"
        sx={{ marginTop: 4 }}
      >
        Pending Requests
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
                  active={orderBy === "requester_staff_id"}
                  direction={orderBy === "requester_staff_id" ? order : "asc"}
                  // onClick={() => handleSortRequest("requester_staff_id")}
                >
                  Requester Staff ID
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "full_name"}
                  direction={orderBy === "full_name" ? order : "asc"}
                  // onClick={() => handleSortRequest("full_name")}
                >
                  Full Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "position"}
                  direction={orderBy === "position" ? order : "asc"}
                  // onClick={() => handleSortRequest("position")}
                >
                  Position
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "dept"}
                  direction={orderBy === "dept" ? order : "asc"}
                  // onClick={() => handleSortRequest("dept")}
                >
                  Dept
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "country"}
                  direction={orderBy === "country" ? order : "asc"}
                  // onClick={() => handleSortRequest("country")}
                >
                  Country
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "email"}
                  direction={orderBy === "email" ? order : "asc"}
                  // onClick={() => handleSortRequest("email")}
                >
                  Email
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "wfh_date"}
                  direction={orderBy === "wfh_date" ? order : "asc"}
                  // onClick={() => handleSortRequest("wfh_date")}
                >
                  WFH Date
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "wfh_type"}
                  direction={orderBy === "wfh_type" ? order : "asc"}
                  // onClick={() => handleSortRequest("wfh_type")}
                >
                  WFH Type
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "approval_status"}
                  direction={orderBy === "approval_status" ? order : "asc"}
                  // onClick={() => handleSortRequest("approval_status")}
                >
                  Approval Status
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "approval_status"}
                  // onClick={() => handleSortRequest("approval_status")}
                >
                  Action
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          {isPending ? (
            <TableBody>
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Box
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    height="100%"
                    margin="16px"
                  >
                    <LoadingSpinner />
                  </Box>
                </TableCell>
              </TableRow>
            </TableBody>
          ) : (
            <TableBody>
              {requests.map((request) => (
                <TableRow key={request.arrangement_id}>
                  <TableCell>{request.requester_staff_id}</TableCell>
                  <TableCell>
                    {employees[request.requester_staff_id]
                      ? `${employees[request.requester_staff_id].staff_fname} ${
                          employees[request.requester_staff_id].staff_lname
                        }`
                      : "Not Available"}
                  </TableCell>
                  <TableCell>
                    {employees[request.requester_staff_id]?.position ||
                      "Not Available"}
                  </TableCell>
                  <TableCell>
                    {employees[request.requester_staff_id]?.dept ||
                      "Not Available"}
                  </TableCell>
                  <TableCell>
                    {employees[request.requester_staff_id]?.country ||
                      "Not Available"}
                  </TableCell>
                  <TableCell>
                    {employees[request.requester_staff_id]?.email ||
                      "Not Available"}
                  </TableCell>
                  <TableCell>{request.wfh_date}</TableCell>
                  <TableCell>{request.wfh_type}</TableCell>
                  <TableCell>
                    <Chip
                      color={getChipColor(
                        request.approval_status as ApprovalStatus
                      )}
                      label={capitalize(request.approval_status)}
                    />
                  </TableCell>
                  <TableCell>
                    <ButtonGroup
                      variant="contained"
                      aria-label="Appprove/Reject group"
                    >
                      <Button color="success">Approve</Button>
                      <Button color="error">Reject</Button>
                    </ButtonGroup>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          )}
        </Table>
      </TableContainer>
    </Container>
  );
};
