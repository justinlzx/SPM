import React from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    ChipProps,
} from "@mui/material";
import { WithdrawButton } from "./WithdrawButton";
import { CancelButton } from "./CancelButton";
import { capitalize } from "../utils/utils";

type TOORequest = {
    arrangement_id: number;
    staff_id: number;
    ooo_start_date: string;
    ooo_end_date?: string;
    reason_description: string;
    approval_status: string;
};

interface OOORequestTableProps {
    requests: TOORequest[];
    handleSuccess: (id: number, action: "cancel" | "withdraw") => void;
}

const getChipColor = (status: string): ChipProps["color"] => {
    switch (status.toLowerCase()) {
        case "approved":
            return "success";
        case "pending":
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

export const OOORequestTable: React.FC<OOORequestTableProps> = ({
    requests,
    handleSuccess,
}) => (
    <TableContainer component={Paper} sx={{ marginTop: 3 }}>
        <Table>
            <TableHead>
                <TableRow>
                    <TableCell>Staff ID</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>End Date</TableCell>
                    <TableCell>Reason</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Action</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {requests.length === 0 ? (
                    <TableRow>
                        <TableCell colSpan={6} align="center">
                            No requests found
                        </TableCell>
                    </TableRow>
                ) : (
                    requests.map((request) => (
                        <TableRow key={request.arrangement_id}>
                            <TableCell>{request.staff_id}</TableCell>
                            <TableCell>{request.ooo_start_date}</TableCell>
                            <TableCell>{request.ooo_end_date || "-"}</TableCell>
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
                                {request.reason_description || "No reason provided"}
                            </TableCell>
                            <TableCell>
                                <Chip
                                    color={getChipColor(request.approval_status)}
                                    label={capitalize(request.approval_status)}
                                />
                            </TableCell>
                            <TableCell>
                                {request.approval_status === "pending" && (
                                    <>
                                        <WithdrawButton
                                            arrangement_id={request.arrangement_id}
                                            onSuccess={(id) => handleSuccess(id, "withdraw")}
                                        />
                                    </>
                                )}
                                {request.approval_status === "approved" && (
                                    <>
                                        <CancelButton
                                            arrangement_id={request.arrangement_id}
                                            onSuccess={(id) => handleSuccess(id, "cancel")}
                                        />
                                    </>
                                )}
                            </TableCell>
                        </TableRow>
                    ))
                )}
            </TableBody>
        </Table>
    </TableContainer>
);