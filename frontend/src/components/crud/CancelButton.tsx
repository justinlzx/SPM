import React, { useState } from "react";
import { 
  Button, 
  Modal, 
  Box, 
  Typography, 
  TextField, 
  CircularProgress 
} from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

interface CancelButtonProps {
  arrangement_id: number;
  onSuccess: (id: number, newStatus: "pending_cancellation") => void;
}

export const CancelButton: React.FC<CancelButtonProps> = ({
  arrangement_id,
  onSuccess,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState<string>("");

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    setOpen(false);
    setReason("");
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setReason(e.target.value);
  };

  const handleCancel = async () => {
    setLoading(true);

    try {
      const approvingOfficer = localStorage.getItem("id");

      if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
      }

      // Payload with the new status
      const payload = new URLSearchParams({
        action: "cancel",
        approving_officer: approvingOfficer,
        reason_description: reason.trim() || "",
        new_status: "pending_cancellation", // Inform backend of the status change
      });

      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        payload,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      console.log("Cancellation request sent successfully");
      onSuccess(arrangement_id, "pending_cancellation"); // Notify parent component
    } catch (error) {
      console.error("Failed to cancel request:", error);
    } finally {
      setLoading(false);
      handleClose();
    }
  };

  return (
    <>
      <Button size="small" variant="outlined" color="primary" onClick={handleOpen}>
        Cancel
      </Button>

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
          <Typography variant="h6">
            Confirm Cancellation
          </Typography>
          <Typography variant="body1">
            Are you sure you want to cancel this request? 
            <br/>
            <br/>
            Your manager will review this cancellation.
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
              onClick={handleCancel}
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

export default CancelButton;
