import React, { useState } from "react";
import { Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Box } from "@mui/material";
import axios from "axios";

interface CancelButtonProps {
arrangement_id: number;
onSuccess: (id: number, action: "cancel") => void;
}

const CancelButton: React.FC<CancelButtonProps> = ({
arrangement_id,
onSuccess,
}) => {
const [loading, setLoading] = useState(false);
const [open, setOpen] = useState(false);

const handleOpen = () => setOpen(true);
const handleClose = () => setOpen(false);

const handleCancel = async () => {
    setLoading(true);
    try {
    const approvingOfficer = localStorage.getItem("id");
    await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/arrangements/${arrangement_id}/status`,
        new URLSearchParams({
        action: "cancel",
        approving_officer: approvingOfficer || "",
        }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );

    onSuccess(arrangement_id, "cancel");
    } catch (error) {
    console.error("Failed to cancel:", error);
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
    <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Confirm Cancellation</DialogTitle>
        <DialogContent>Are you sure you want to cancel this request?</DialogContent>
        <DialogActions>
        <Button onClick={handleClose} color="secondary">No</Button>
        <Button onClick={handleCancel} color="primary">
            {loading ? <CircularProgress size={24} /> : "Yes"}
        </Button>
        </DialogActions>
    </Dialog>
    </>
);
};

export default CancelButton;
