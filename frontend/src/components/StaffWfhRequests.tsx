import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  ChipProps,
  Modal,
  Box,
  Typography,
  CircularProgress,
  TextField,
} from "@mui/material";
import axios from "axios";
import { capitalize } from "../utils/utils";
import { ApprovalStatus } from "../types/ApprovalStatus"; 

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  staff_id: number;
  wfh_date: string;
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  approval_status: ApprovalStatus;  
};

interface StaffWfhRequestsProps {
  requests: TWFHRequest[];
  handleSuccess: (id: number, action: "cancel" | "withdraw") => void;
}

const getChipColor = (status: ApprovalStatus | undefined): ChipProps["color"] => {
  if (!status) return "default";
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.PendingApproval:
    case ApprovalStatus.PendingWithdrawal:
      return "warning";
    case ApprovalStatus.Rejected:
      return "error";
    default:
      return "default";
  }
};

export const StaffWfhRequests: React.FC<StaffWfhRequestsProps> = ({
  requests,
  handleSuccess,
}) => {
  const [open, setOpen] = useState(false);
  const [action, setAction] = useState<"cancel" | "withdraw">();
  const [selectedArrangementId, setSelectedArrangementId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState<string>("");

  const handleOpen = (arrangementId: number, action: "cancel" | "withdraw") => {
    setSelectedArrangementId(arrangementId);
    setAction(action);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedArrangementId(null);
    setAction(undefined);
    setReason("");
  };

  const handleConfirmAction = async () => {
    if (!selectedArrangementId || !action) return;
    setLoading(true);
    try {
      const approvingOfficer = localStorage.getItem("id");
      if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
      }
      // Build the payload for the backend
      const payload = new URLSearchParams({
        action: action,
        approving_officer: approvingOfficer,
        reason_description: action === "withdraw" ? reason : "Withdraw Request",
        new_status: action === "withdraw" ? "pending withdrawal" : "cancelled",
      });

      console.log(payload)

      await axios.put(
        `${BACKEND_URL}/arrangements/${selectedArrangementId}/status`,
        payload,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      const updatedRequest = await fetchUpdatedStatus(selectedArrangementId);
      console.log(`${action} action successful`);
      handleSuccess(selectedArrangementId, action);
    } catch (error) {
      console.error(`Failed to ${action} request:`, error);
    } finally {
      setLoading(false);
      handleClose();
    }
  };

  const fetchUpdatedStatus = async (arrangementId: number) => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/arrangements/${arrangementId}`
      ); 
      return response.data.data; 
    } catch (error) {
      console.error("Failed to fetch updated request:", error);
      return null; 
    }
  }

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
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No requests found
                </TableCell>
              </TableRow>
            ) : (
              requests.map((request) => (
                <TableRow key={request.arrangement_id}>
                  <TableCell>{request.staff_id}</TableCell>
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
                      padding: 1,
                    }}
                  >
                    {request.reason_description || "Withdraw Request"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      color={getChipColor(request.approval_status)} 
                      label={request.approval_status ? capitalize(request.approval_status) : "Unknown"}
                      variant={request.approval_status === ApprovalStatus.PendingWithdrawal ? "outlined" : "filled"}
                    />
                  </TableCell>
                  <TableCell>
                    {request.approval_status === ApprovalStatus.PendingApproval && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="primary"
                        onClick={() => handleOpen(request.arrangement_id, "cancel")}
                      >
                        Cancel
                      </Button>
                    )}
                    {request.approval_status === ApprovalStatus.Approved && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="secondary"
                        onClick={() => handleOpen(request.arrangement_id, "withdraw")}
                      >
                        Withdraw
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Confirmation Dialog */}
      <Modal open={open} onClose={handleClose}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 400,
            bgcolor: "background.paper",
            borderRadius: 2,
            p: 4,
            boxShadow: 24,
          }}
        >
          <Typography variant="h6">
            Confirm {action === "cancel" ? "Cancellation" : "Withdrawal"}
          </Typography>
          <Typography mb={2}>
            Are you sure you want to{" "}
            {action === "cancel" ? "cancel" : "withdraw"} this request?
          </Typography>
          {action === "withdraw" && (
            <TextField
              label="Reason for withdrawal (Optional)"
              fullWidth
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              margin="normal"
            />
          )}

          <Box mt={2} display="flex" justifyContent="flex-end">
            <Button
              onClick={handleClose}
              variant="outlined"
              color="secondary"
              sx={{ mr: 2 }}
            >
              No
            </Button>
            <Button
              onClick={handleConfirmAction}
              variant="contained"
              color="primary"
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : "Yes"}
            </Button>
          </Box>
        </Box>
      </Modal>
    </>
  );
};
