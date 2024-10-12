import React from "react";
import { Button } from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type CancelButtonProps = {
arrangement_id: number;
onSuccess: (id: number) => void;
};

export const CancelButton: React.FC<CancelButtonProps> = ({
arrangement_id,
onSuccess,
}) => {
const handleCancel = async () => {
    try {
    const approvingOfficer = localStorage.getItem("id");

    if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
    }

    await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        new URLSearchParams({
        action: "cancel",
        approving_officer: approvingOfficer,
        reason_description: "",
        }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );

    console.log("Cancel successful");
    onSuccess(arrangement_id); // Notify parent on success
    } catch (error) {
    console.error("Failed to cancel request:", error);
    }
};

return (
    <Button size="small" variant="outlined" color="primary" onClick={handleCancel}>
    Cancel
    </Button>
);
};
