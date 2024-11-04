import React, { useContext, useEffect, useState } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { useNavigate } from "react-router-dom";
import {
    Box,
    Container,
    Typography,
    Divider,
    Snackbar,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    TextField,
    Chip,
    TablePagination,
    CircularProgress,
} from "@mui/material";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
    arrangement_id: number;
    wfh_date: string;
    wfh_type: string;
    approval_status: string;
    reason_description: string;
};

const getChipColor = (status: string | undefined) => {
    if (!status) return "default"; // Default if status is undefined
    switch (status.toLowerCase()) {
        case "approved":
            return "success";
        case "pending":
            return "warning";
        case "rejected":
            return "error";
        default:
            return "default";
    }
};

export const RequestHistoryPage: React.FC = () => {
    const { user } = useContext(UserContext);
    const [logs, setLogs] = useState<TWFHRequest[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState("");
    const [alertStatus, setAlertStatus] = useState<"success" | "error">("success");
    const navigate = useNavigate();

    useEffect(() => {
        if (!user) {
            navigate("/login");
            return;
        }
        fetchLogs();
    }, [user, navigate]);

    const handleCloseSnackBar = () => setShowSnackbar(false);

    const fetchLogs = async () => {
        try {
            const response = await axios.get(`${BACKEND_URL}/arrangements/logs/all`);
            const fetchedLogs = response.data.data; // Adjust the path as necessary
            setLogs(fetchedLogs);
        } catch (error) {
            console.error("Error fetching arrangement logs:", error);
            setAlertStatus("error");
            setSnackbarMessage("Failed to load Request History.");
            setShowSnackbar(true);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        setPage(0); // Reset to first page when searching
    };

    const filteredLogs = logs.filter(
        (log) =>
            log.reason_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            log.wfh_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            log.approval_status?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleChangePage = (_event: unknown, newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                <CircularProgress />
            </div>
        );
    }

    return (
        <Container maxWidth="md">
            <Typography variant="h4" sx={{ mb: 2 }}>
                Department Request History
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <TextField
                label="Search by reason, type or status"
                variant="outlined"
                fullWidth
                margin="normal"
                value={searchTerm}
                onChange={handleSearch}
            />

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Requester</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Approver</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredLogs.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    {searchTerm ? "No matching requests found" : "No requests available"}
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredLogs
                                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                                .map((log) => {
                                    console.log("Log entry:", log); // Log each log entry for debugging

                                    // Ensure log.approval_status is a string before accessing it
                                    const approvalStatus = log.approval_status || "N/A"; // Fallback to "N/A" if undefined
                                    const formattedStatus = typeof approvalStatus === 'string' ? approvalStatus.charAt(0).toUpperCase() + approvalStatus.slice(1) : approvalStatus;

                                    return (
                                        <TableRow key={log.arrangement_id}>
                                            <TableCell>
                                                <Chip
                                                    color={getChipColor(approvalStatus)}
                                                    label={formattedStatus}
                                                />
                                            </TableCell>
                                            <TableCell>{log.wfh_type?.toUpperCase() || "N/A"}</TableCell>
                                            <TableCell>{new Date(log.wfh_date).toLocaleDateString() || "N/A"}</TableCell>
                                            <TableCell>{log.reason_description || "N/A"}</TableCell>
                                        </TableRow>
                                    );
                                })
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <TablePagination
                component="div"
                rowsPerPageOptions={[10, 20, 30]}
                count={filteredLogs.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
            />

            {/* Snackbar for alerts */}
            <Snackbar
                open={showSnackbar}
                onClose={handleCloseSnackBar}
                anchorOrigin={{ vertical: "top", horizontal: "center" }}
                autoHideDuration={6000}
            >
                <Alert onClose={handleCloseSnackBar} severity={alertStatus}>
                    {snackbarMessage}
                </Alert>
            </Snackbar>
        </Container>
    );
};

export default RequestHistoryPage;