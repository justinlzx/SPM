import React from "react";
import { Button } from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type WithdrawButtonProps = {
arrangement_id: number;
onSuccess: (id: number) => void;
};

export const WithdrawButton: React.FC<WithdrawButtonProps> = ({
arrangement_id,
onSuccess,
}) => {
const handleWithdraw = async () => {
    try {
    const approvingOfficer = localStorage.getItem("id");

    if (!approvingOfficer) {
        console.error("Approving officer ID not found.");
        return;
    }

    await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        new URLSearchParams({
        action: "withdraw",
        approving_officer: approvingOfficer,
        reason_description: "",
        }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );

    console.log("Withdraw successful");
    onSuccess(arrangement_id); // Notify parent on success
    } catch (error) {
    console.error("Failed to withdraw request:", error);
    }
};

return (
    <Button
    size="small"
    variant="contained"
    sx={{ backgroundColor: "grey.500", color: "white" }}
    onClick={handleWithdraw}
    >
    Withdraw
    </Button>
);
};
