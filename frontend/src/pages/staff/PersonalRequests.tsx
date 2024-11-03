import React, { useEffect, useState, useContext } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
} from "@mui/material";
import axios from "axios";
import { UserContext } from "../../context/UserContextProvider";
import { ApprovalStatus } from "../../types/status";
import { capitalize } from "../../utils/utils";

const getChipColor = (status: ApprovalStatus) => {
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.Rejected:
      return "error";
    case ApprovalStatus.PendingApproval:
    case ApprovalStatus.PendingWithdrawal:
      return "warning";
    default:
      return "default";
  }
};
import { TWFHRequest } from "../../types/requests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const PersonalRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [approvedCount, setApprovedCount] = useState<number>(0);
  const [approvedThisMonth, setApprovedThisMonth] = useState<number>(0);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );

        const allRequests: TWFHRequest[] = response.data.data;
        setRequests(allRequests);

        // Calculate approved requests count
        const approvedRequestsCount = allRequests.filter(
          (request) => request.current_approval_status === ApprovalStatus.Approved
        ).length;
        setApprovedCount(approvedRequestsCount);

        // Calculate approved WFH days for the current month
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
        const approvedThisMonthCount = allRequests.filter((request) => {
          const requestDate = new Date(request.wfh_date);
          return (
            request.current_approval_status === ApprovalStatus.Approved &&
            requestDate.getMonth() === currentMonth &&
            requestDate.getFullYear() === currentYear
          );
        }).length;

        setApprovedThisMonth(approvedThisMonthCount);

      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRequests();
  }, [userId]);

  return (
    <>
      <TableContainer component={Paper} sx={{ marginTop: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Staff ID</TableCell>
              <TableCell>Start Date</TableCell>
              <TableCell>End Date</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No requests found
                </TableCell>
              </TableRow>
            ) : (
              requests.map((request) => (
                <TableRow key={request.arrangement_id}>
                  <TableCell>{request.requester_staff_id}</TableCell>
                  <TableCell>{request.wfh_date}</TableCell>
                  <TableCell>{request.end_date || "-"}</TableCell>
                  <TableCell>{request.wfh_type?.toUpperCase() || "-"}</TableCell>
                  <TableCell
                    sx={{
                      maxWidth: "200px",
                      wordBreak: "break-word",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {request.reason_description || "-"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      color={getChipColor(request.current_approval_status)}
                      label={capitalize(
                        request.current_approval_status
                          ? request.current_approval_status
                          : "Unknown Status"
                      )}
                      variant={
                        request.current_approval_status ===
                        ApprovalStatus.PendingWithdrawal
                          ? "outlined"
                          : "filled"
                      }
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};

export default PersonalRequests;
