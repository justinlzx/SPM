import React, { useState } from "react";
import { Button, Modal, Box, Typography, CircularProgress } from "@mui/material";
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
  const [open, setOpen] = useState(false); // Manage modal open/close state
  const [loading, setLoading] = useState(false); // Manage loading state

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  // API call to update the backend state on withdrawal
  const handleWithdraw = async () => {
    setLoading(true); // Show loading indicator
    try {
      const approvingOfficer = localStorage.getItem("id");
      if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
      }

      // Send the withdraw request to the backend
      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        new URLSearchParams({
          action: "withdraw",
          approving_officer: approvingOfficer, // Include officer's ID
        }),
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
      {/* Button to open the withdraw confirmation modal */}
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
          <Typography variant="body1" mb={2}>
            Are you sure you want to withdraw this request?
            <br />
            <br />
            This action cannot be undone.
          </Typography>
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
