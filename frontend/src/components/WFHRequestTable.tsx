import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Modal,
  Box,
  Typography,
  TextField,
  CircularProgress,
  Chip,
  ChipProps,
} from "@mui/material";
import axios from "axios";
import { capitalize } from "../utils/utils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  staff_id: number;
  wfh_date: string;
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  approval_status: string;
};

interface WFHRequestTableProps {
  requests: TWFHRequest[];
  handleSuccess: (id: number, action: "cancel" | "withdraw") => void;
}

const getChipColor = (status: string): ChipProps["color"] => {
  switch (status.toLowerCase()) {
    case "approved":
      return "success";
    case "pending approval":
    case "pending withdrawal":
      return "warning";
    case "rejected":
      return "error";
    case "cancelled":
    case "withdrawn":
      return "default";
    default:
      return "primary";
  }
};

export const WFHRequestTable: React.FC<WFHRequestTableProps> = ({
  requests,
  handleSuccess,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState<string>("");
  const [currentAction, setCurrentAction] = useState<"cancel" | "withdraw">();
  const [selectedArrangementId, setSelectedArrangementId] = useState<number | null>(null);

  const handleOpen = (arrangementId: number, action: "cancel" | "withdraw") => {
    setSelectedArrangementId(arrangementId);
    setCurrentAction(action);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setReason("");
    setLoading(false);
    setSelectedArrangementId(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setReason(e.target.value);
  };

  const handleSubmitAction = async () => {
    if (!selectedArrangementId || !currentAction) return;
    setLoading(true);

    try {
      const approvingOfficer = localStorage.getItem("id");
      if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
      }

      const payload = new URLSearchParams({
        action: currentAction,
        approving_officer: approvingOfficer,
        reason_description: reason.trim() || "",
        new_status: currentAction === "cancel" ? "pending cancellation" : "pending withdrawal",
      });

      await axios.put(
        `${BACKEND_URL}/arrangements/${selectedArrangementId}/status`,
        payload,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      console.log(`${currentAction} action successful`);
      handleSuccess(selectedArrangementId, currentAction);
    } catch (error) {
      console.error(`Failed to ${currentAction} request:`, error);
    } finally {
      setLoading(false);
      handleClose();
    }
  };


  const renderActionButton = (request: TWFHRequest) => {
    if (request.approval_status === "pending approval") {
      return (
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={() => handleOpen(request.arrangement_id, "cancel")}
        >
          Cancel
        </Button>
      );
    } else if (request.approval_status === "approved") {
      return (
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={() => handleOpen(request.arrangement_id, "withdraw")}
        >
          Withdraw
        </Button>
      );
    } else if (request.approval_status === "pending cancellation" || request.approval_status === "pending withdrawal") {
      return <Chip label={capitalize(request.approval_status)} color="warning" />;
    } else {
      return null;
    }
  };

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
                  <TableCell>{request.wfh_type.toUpperCase()}</TableCell>
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
                    {request.reason_description || "-"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      color={getChipColor(request.approval_status)}
                      label={capitalize(request.approval_status)}
                    />
                  </TableCell>
                  <TableCell>{renderActionButton(request)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Modal open={open} onClose={handleClose}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 500,
            bgcolor: "background.paper",
            boxShadow: 24,
            p: 4,
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" mb={2}>
            Confirm {currentAction === "cancel" ? "Cancellation" : "Withdrawal"}
          </Typography>
          <Typography variant="body1">
            Are you sure you want to {currentAction === "cancel" ? "cancel" : "withdraw"} this request?
            This action cannot be undone.
          </Typography>
          <TextField
            fullWidth
            label="Reason (optional)"
            variant="outlined"
            value={reason}
            onChange={handleInputChange}
            margin="normal"
          />
          <Box mt={2} display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined" color="secondary" onClick={handleClose} disabled={loading}>
              No
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmitAction}
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
