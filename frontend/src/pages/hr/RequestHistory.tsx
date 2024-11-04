import React, { useContext, useEffect, useState } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { useNavigate } from "react-router-dom";
import {
    Box,
    Container,
    Typography,
    Divider,
    Button,
    Snackbar,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
} from "@mui/material";
import { SnackBarComponent, AlertStatus } from "../../common/SnackBar";
import axios from "axios";

export const RequestHistoryPage: React.FC = () => {
    const { user } = useContext(UserContext);
    const [logs, setLogs] = useState<any[]>([]);
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState("");
    const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Info);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

    if (!user) {
        return (
            <Typography variant="h4">Please log in to access this page</Typography>
        );
    }

    // Function to handle Snackbar close
    const handleCloseSnackBar = () => setShowSnackbar(false);

    // Function to fetch arrangement logs
    const fetchLogs = async () => {
        try {
            const response = await axios.get(`${BACKEND_URL}/arrangements/logs/all`, {
            });

            setLogs(response.data);
        } catch (error) {
            console.error("Error fetching arrangement logs:", error);
            setAlertStatus(AlertStatus.Error);
            setSnackbarMessage("Failed to load Request History.");
            setShowSnackbar(true);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    return (
        <Container maxWidth="md">
            <Typography variant="h4" sx={{ mb: 2 }}>
                WFH Request History
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Reason</TableCell>
                            <TableCell>Status</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {logs.map((log) => (
                            <TableRow key={log.id}>
                                <TableCell>{new Date(log.date).toLocaleDateString()}</TableCell>
                                <TableCell>{log.type}</TableCell>
                                <TableCell>{log.reason}</TableCell>
                                <TableCell>{log.status}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

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