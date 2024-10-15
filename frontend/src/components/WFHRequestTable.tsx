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
import { WithdrawButton } from "./crud/WithdrawButton";
import { CancelButton } from "./crud/CancelButton";
import { capitalize } from "../utils/utils";

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

export const WFHRequestTable: React.FC<WFHRequestTableProps> = ({
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
                        //existingPayload={request}
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
