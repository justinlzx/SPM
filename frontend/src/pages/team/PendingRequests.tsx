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
import {
  useArrangement,
  useUpdateArrangement,
} from "../../hooks/auth/arrangement/arrangement";
import { UserContext } from "../../context/UserContextProvider";
import { TRequest } from "../../hooks/auth/arrangement/arrangement.utils";
import { TEmployee } from "../../hooks/auth/employee/employee.utils";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import { capitalize } from "../../utils/utils";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";

// Define types

type TOrder = "asc" | "desc";
type TAction = "approve" | "reject";

enum ApprovalStatus {
  Approved = "approved",
  Pending = "pending",
  Rejected = "rejected",
}

type TWFHRequest = Partial<TRequest> & {
  requester_info: TEmployee;
};

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
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [order, setOrder] = useState<TOrder>("asc");
  const [orderBy, setOrderBy] = useState<
    keyof TWFHRequest | "requester_staff_id"
  >("requester_staff_id"); // Default sorting by staff ID
  const [searchTerm, setSearchTerm] = useState(""); // New state for search term

  const { mutateAsync: arrangementMutation, isPending } = useArrangement();
  const { mutateAsync: updateArrangementMutation } = useUpdateArrangement();
  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchRequests = async () => {
      if (!user) return;
      const result = await arrangementMutation({
        id: user.id,
        status: "pending",
      });
      setRequests(result! as TWFHRequest[]);
    };
    fetchRequests();
  }, [setRequests, arrangementMutation, user]);

  const handleRequestAction = async (
    action: TAction,
    arrangement_id: number
  ) => {
    const update = await updateArrangementMutation({
      updatedStatus: action,
      arrangement_id,
    });

    console.log(update);

    if (update) {
      console.log("Request updated successfully");
    }
  };

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
                // active={orderBy === "full_name"}
                // direction={orderBy === "full_name" ? order : "asc"}
                // onClick={() => handleSortRequest("full_name")}
                >
                  Full Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                // active={orderBy === "position"}
                // direction={orderBy === "position" ? order : "asc"}
                // onClick={() => handleSortRequest("position")}
                >
                  Position
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                // active={orderBy === "dept"}
                // direction={orderBy === "dept" ? order : "asc"}
                // onClick={() => handleSortRequest("dept")}
                >
                  Dept
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                // active={orderBy === "country"}
                // direction={orderBy === "country" ? order : "asc"}
                // onClick={() => handleSortRequest("country")}
                >
                  Country
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                // active={orderBy === "email"}
                // direction={orderBy === "email" ? order : "asc"}
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
              {requests.map((request: TWFHRequest) => {
                console.log(request);
                const {
                  arrangement_id,
                  wfh_date,
                  wfh_type,
                  approval_status,
                  requester_info: {
                    staff_id,
                    staff_fname,
                    staff_lname,
                    country,
                    email,
                    dept,
                    position,
                  },
                } = request;

                return (
                  <TableRow key={arrangement_id}>
                    <TableCell>{staff_id}</TableCell>
                    <TableCell>{staff_fname + " " + staff_lname}</TableCell>
                    <TableCell>{position}</TableCell>
                    <TableCell>{dept || "Not Available"}</TableCell>
                    <TableCell>{country || "Not Available"}</TableCell>
                    <TableCell>{email || "Not Available"}</TableCell>
                    <TableCell>{wfh_date}</TableCell>
                    <TableCell>{wfh_type!.toUpperCase()}</TableCell>
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
                          // variant="contained"
                          color="success"
                          startIcon={<CheckIcon />}
                          onClick={() =>
                            handleRequestAction("approve", arrangement_id!)
                          }
                        >
                          Approve
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<CloseIcon />}
                          onClick={() =>
                            handleRequestAction("reject", arrangement_id!)
                          }
                        >
                          Reject
                        </Button>
                      </ButtonGroup>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          )}
        </Table>
      </TableContainer>
    </Container>
  );
};
