import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import {
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Button,
  ButtonGroup,
  Chip,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { capitalize } from "../../utils/utils";
import { SnackBarComponent, AlertStatus } from "../../common/SnackBar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TAction = "accepted" | "rejected";

enum DelegationStatus {
  Accepted = "accepted",
  Pending = "pending",
  Rejected = "rejected",
}

type TDelegationRequest = {
  date_of_delegation: string;
  full_name: string;
  staff_id: number;
  delegate_manager_id: number;
  status_of_delegation: DelegationStatus;
};

export const PendingDelegations = () => {
  const [requests, setRequests] = useState<TDelegationRequest[]>([]);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  // Snackbar state
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Success);

  // Modal state
  const [openRejectModal, setOpenRejectModal] = useState(false);
  const [reason, setReason] = useState("");
  const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);

  useEffect(() => {
    const fetchPendingDelegationRequests = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/employees/manager/viewdelegations/${userId}`,
          {
            params: {
              status: "pending",
            },
          }
        );
        const delegationRequests: TDelegationRequest[] = response.data.pending_approval_delegations || [];
        setRequests(delegationRequests);
      } catch (error) {
        console.error("Failed to fetch delegation requests:", error);
      }
    };
    fetchPendingDelegationRequests();
  }, [user, userId]);

  const handleDelegationAction = async (action: TAction, staff_id: number, reason?: string) => {
    try {
      await axios.put(
        `${BACKEND_URL}/employees/manager/delegate/${staff_id}/status`,
        { description: reason },
        {
          params: { status: action },
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        }
      );

      setSnackbarMessage(`Delegation request ${action} successfully!`);
      setAlertStatus(AlertStatus.Success);
      setShowSnackbar(true);

      setRequests((prevRequests) =>
        prevRequests.filter((req) => req.staff_id !== staff_id)
      );

      setOpenRejectModal(false);
      setReason("");
    } catch (error) {
      console.error(`Error processing delegation request:`, error);
      setSnackbarMessage(`Error processing delegation request.`);
      setAlertStatus(AlertStatus.Error);
      setShowSnackbar(true);
    }
  };

  const handleOpenRejectModal = (staff_id: number) => {
    setSelectedStaffId(staff_id);
    setOpenRejectModal(true);
  };

  const handleCloseRejectModal = () => {
    setOpenRejectModal(false);
    setReason("");
  };

  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
  };

  return (
    <Container>
      <Typography variant="h6" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Delegation Requests
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Delegator Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Delegator Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Date of Delegation</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Delegation Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No pending delegation requests
                </TableCell>
              </TableRow>
            ) : (
              requests.map((request) => {
                const { staff_id, full_name, date_of_delegation, status_of_delegation } = request;
                return (
                  <TableRow key={staff_id}>
                    <TableCell>{staff_id}</TableCell>
                    <TableCell>{full_name}</TableCell>
                    <TableCell>{new Date(date_of_delegation).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={capitalize(status_of_delegation)}
                        color={
                          status_of_delegation === DelegationStatus.Accepted
                            ? "success"
                            : status_of_delegation === DelegationStatus.Rejected
                            ? "error"
                            : "warning"
                        }
                      />
                    </TableCell>
                    <TableCell>
                      {status_of_delegation === DelegationStatus.Pending ? (
                        <ButtonGroup variant="contained" aria-label="Accept/Reject Button group">
                          <Tooltip title="Accept delegation">
                            <Button
                              size="small"
                              color="success"
                              startIcon={<CheckIcon />}
                              onClick={() => handleDelegationAction("accepted", staff_id)}
                            >
                              Accept
                            </Button>
                          </Tooltip>
                          <Tooltip title="Reject delegation">
                            <Button
                              size="small"
                              color="error"
                              startIcon={<CloseIcon />}
                              onClick={() => handleOpenRejectModal(staff_id)}
                            >
                              Reject
                            </Button>
                          </Tooltip>
                        </ButtonGroup>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Reject Modal */}
      <Dialog open={openRejectModal} onClose={handleCloseRejectModal} maxWidth="sm" fullWidth>
        <DialogTitle>Reject Delegation</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Reason for Rejection"
            type="text"
            fullWidth
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ m: 2 }}>
          <Button onClick={handleCloseRejectModal} color="secondary">
            Cancel
          </Button>
          <Button
            onClick={() => handleDelegationAction("rejected", selectedStaffId!, reason)}
            variant="outlined"
            color="error"
            disabled={!reason.trim()}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      <SnackBarComponent
        showSnackbar={showSnackbar}
        handleCloseSnackBar={handleCloseSnackBar}
        alertStatus={alertStatus}
        snackbarMessage={snackbarMessage}
      />
    </Container>
  );
};

export default PendingDelegations;
