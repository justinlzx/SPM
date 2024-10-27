import React, { useEffect, useState, useContext } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
} from "@mui/material";
import axios from "axios";
import { UserContext } from "../../context/UserContextProvider";
import { ApprovalStatus } from "../../types/ApprovalStatus";
import { capitalize } from "../../utils/utils";


const getChipColor = (status: ApprovalStatus): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status) {
        case ApprovalStatus.Approved:
            return "success";
        case ApprovalStatus.Rejected:
            return "error";
        case ApprovalStatus.PendingApproval:
            case ApprovalStatus.PendingWithdrawal:
            return "warning";
        default:
            return "default";
    }
};
import { TWFHRequest } from "../../types/requests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;



export const PersonalRequests = () => {
    const [requests, setRequests] = useState<TWFHRequest[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const { user } = useContext(UserContext);
    const userId = user!.id;

useEffect(() => {
    const fetchRequests = async () => {
    try {
        const response = await axios.get(
        `${BACKEND_URL}/arrangements/personal/${userId}`
        );

        const allRequests: TWFHRequest[] = response.data.data.map(
        (request: any) => ({
            ...request,
            approval_status: ApprovalStatus[request.approval_status as keyof typeof ApprovalStatus],
            wfh_date: new Date(request.wfh_date),
        })
        );

        setRequests(allRequests);
    } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
    } finally {
        setLoading(false);
    }
    };

    fetchRequests();
}, [userId]);

return (
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
        </TableRow>
        </TableHead>
        <TableBody>
        {loading ? (
            <TableRow>
            <TableCell colSpan={6} align="center">
                Loading...
            </TableCell>
            </TableRow>
        ) : requests.length === 0 ? (
            <TableRow>
            <TableCell colSpan={6} align="center">
                No requests found
            </TableCell>
            </TableRow>
        ) : (
            requests.map((request) => (
            <TableRow key={request.arrangement_id}>
                <TableCell>{request.staff_id}</TableCell>
                <TableCell>{request.wfh_date.toISOString()}</TableCell>
                {/* <TableCell>{request.end_date || "-"}</TableCell> */}
                <TableCell>{request.wfh_type?.toUpperCase() || "-"}</TableCell>
                <TableCell sx={{ maxWidth: "200px", wordBreak: "break-word", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {request.reason_description || "-"}
                </TableCell>
                <TableCell>
                <Chip
                    color={getChipColor(request.approval_status)}
                    label={capitalize(request.approval_status.toString())}
                    variant={
                    request.approval_status === ApprovalStatus.PendingWithdrawal
                        ? "outlined"
                        : "filled"
                    }
                />
                </TableCell>
            </TableRow>
            ))
        )}
        </TableBody>
    </Table>
    </TableContainer>
);
};
