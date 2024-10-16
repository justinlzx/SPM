import React, { useState } from "react";
import { Button, 
  Modal, 
  Box, 
  Typography,
  TextField, 
  CircularProgress } from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL; // Ensure this URL is set in your environment

interface WithdrawButtonProps {
  arrangement_id: number;
  onSuccess: (id: number, action: "withdraw") => void;
}

export const WithdrawButton: React.FC<WithdrawButtonProps> = ({
  arrangement_id,
  onSuccess,
}) => {
  const [open, setOpen] = useState(false); 
  const [loading, setLoading] = useState(false); 
  const [reason, setReason] = useState<string>("");

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    setOpen(false)
    setReason("");
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setReason(e.target.value);
  };

 
  const handleWithdraw = async () => {
    setLoading(true); // Show loading indicator
    try {
      const approvingOfficer = localStorage.getItem("id");
      if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
      }

      // Send a PUT request to the backend to withdraw the request
      const payload = new URLSearchParams({
        action: "withdraw",
        approving_officer: approvingOfficer,
        reason_description: reason.trim() || "",
        new_status: "withdrawn", 
      });
      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        payload,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      console.log("Withdrawal successful");
      onSuccess(arrangement_id, "withdraw"); // Notify parent of success
    } catch (error) {
      console.error("Failed to withdraw request:", error);
    } finally {
      setLoading(false); // Stop loading indicator
      handleClose(); // Close the modal
    }
  };

  return (
    <>
      <Button size="small" variant="outlined" color="primary" onClick={handleOpen}>
        Withdraw
      </Button>

      {/* Withdraw confirmation modal */}
      <Modal open={open} onClose={handleClose}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 400,
            bgcolor: "background.paper",
            boxShadow: 24,
            p: 4,
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" mb={2}>
            Confirm Withdrawal
          </Typography>
          <Typography variant="body1">
            Are you sure you want to withdraw this request?
            <br />
            <br />
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
              onClick={handleWithdraw}
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

export default WithdrawButton;
