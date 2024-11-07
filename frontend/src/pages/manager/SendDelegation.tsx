import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import {
  Button,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Tooltip
} from '@mui/material';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import { SelectChangeEvent } from '@mui/material';
import { SnackBarComponent, AlertStatus } from '../../common/SnackBar';
import { UserContext } from '../../context/UserContextProvider';
import { capitalize } from "../../utils/utils";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import { DelegationStatus, TDelegationLog, Peer } from "../../types/delegation";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const SendDelegation: React.FC = () => {
  const { user } = useContext(UserContext);
  const userId = user!.id;
  const [peers, setPeers] = useState<Peer[]>([]);
  const [selectedPeer, setSelectedPeer] = useState('');
  const [snackbar, setSnackbar] = useState({
    showSnackbar: false,
    snackbarMessage: '',
    alertStatus: AlertStatus.Info,
  });
  const [openModal, setOpenModal] = useState(false);
  const [delegationLogs, setDelegationLogs] = useState<TDelegationLog[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDelegationLogs = async () => {
    if (!user || !userId) return;
    setLoading(true);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/employees/manager/viewalldelegations/${userId}`
      );
      const sentDelegations: TDelegationLog[] = response.data.sent_delegations || [];
      setDelegationLogs(sentDelegations);
    } catch (error) {
      console.error("Failed to fetch delegation logs:", error);
      handleSnackbar(AlertStatus.Error, 'Failed to load delegation logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchPeers = async () => {
      if (userId) {
        setLoading(true);
        try {
          const response = await axios.get(`${BACKEND_URL}/employees/manager/peermanager/${userId}`);
          const peers = response.data.peer_employees
            .filter((peer: any) => peer.staff_id !== userId)
            .map((peer: any) => ({
              staff_id: peer.staff_id,
              name: `${peer.staff_fname} ${peer.staff_lname}`,
            }));
          setPeers(peers);
        } catch (error) {
          console.error('Error fetching peers:', error);
          handleSnackbar(AlertStatus.Error, 'Failed to load peers.');
        } finally {
          setLoading(false);
        }
      }
    };

    fetchPeers();
    fetchDelegationLogs();
  }, [user]);

  const hasPendingOrActiveDelegation = delegationLogs.some(
    (log) =>
      log.status_of_delegation === DelegationStatus.Pending ||
      log.status_of_delegation === DelegationStatus.Accepted
  );

  const handlePeerSelect = (event: SelectChangeEvent<string>) => {
    setSelectedPeer(event.target.value);
  };

  const handleDelegate = async () => {
    const existingDelegation = delegationLogs.find(
      (log) =>
        log.delegate_manager_id === parseInt(selectedPeer) &&
        (log.status_of_delegation === DelegationStatus.Pending || log.status_of_delegation === DelegationStatus.Accepted)
    );

    if (existingDelegation) {
      handleSnackbar(
        AlertStatus.Error,
        'This peer already has an active or pending delegation. Please select a different manager.'
      );
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/employees/manager/delegate/${userId}`, null, {
        params: {
          delegate_manager_id: selectedPeer,
        },
      });

      handleSnackbar(AlertStatus.Success, 'Request to delegate peer manager sent');
      setOpenModal(false);
      await fetchDelegationLogs(); // Refresh data after sending delegation
    } catch (error) {
      console.error('Error delegating peer:', error);
      handleSnackbar(AlertStatus.Error, 'Failed to delegate peer as manager.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelDelegation = async (delegateManagerId: number) => {
    setLoading(true);
    try {
      await axios.put(`${BACKEND_URL}/employees/manager/undelegate/${userId}`, {
        params: { delegate_manager_id: delegateManagerId },
      });
      handleSnackbar(AlertStatus.Success, 'Delegation canceled successfully.');
      await fetchDelegationLogs(); // Refresh data after canceling delegation
    } catch (error) {
      console.error('Error canceling delegation:', error);
      handleSnackbar(AlertStatus.Error, 'Failed to cancel delegation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSnackbar = (status: AlertStatus, message: string) => {
    setSnackbar({
      showSnackbar: true,
      snackbarMessage: message,
      alertStatus: status,
    });
  };

  const handleCloseSnackBar = () => {
    setSnackbar((prevState) => ({
      ...prevState,
      showSnackbar: false,
    }));
  };

  const handleOpenModal = () => {
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
  };

  return (
    <Container>
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <LoadingSpinner open={loading} />
        </Box>
      ) : (
        <>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="space-between"
            sx={{ my: 4, gap: 2, p: 2, borderRadius: 1, bgcolor: '#EDEDED' }}
          >
            <Box display="flex" alignItems="center" gap={2}>
              <NotificationsNoneIcon />
              <Box display="flex" flexDirection="column">
                <Typography variant="body2" style={{ color: 'black' }}>
                  You can only delegate to one person at a single time.
                </Typography>
                <Typography variant="caption" style={{ color: 'grey' }}>
                  To withdraw a delegation, click 'Cancel'.
                </Typography>
              </Box>
            </Box>

            <Tooltip
              title={
                hasPendingOrActiveDelegation
                  ? "You have a pending delegation in progress."
                  : ""
              }
            >
              <span>
                <Button
                  variant="outlined"
                  color="primary"
                  data-cy="Delegate-A-Manager"
                  onClick={handleOpenModal}
                  disabled={hasPendingOrActiveDelegation}
                >
                  Delegate a Manager
                </Button>
              </span>
            </Tooltip>
          </Box>

          <Typography variant="h6">Sent Delegations</Typography>
          <Dialog open={openModal} onClose={handleCloseModal}>
            <DialogTitle>Delegate a Peer for Manager Responsibilities</DialogTitle>
            <DialogContent>
              <FormControl fullWidth sx={{ my: 2 }}>
                <InputLabel id="select-peer-label">Select Manager</InputLabel>
                <Select
                  data-cy="select-peer-dropdown"
                  labelId="select-peer-label"
                  label="Select Manager"
                  value={selectedPeer}
                  onChange={handlePeerSelect}
                >
                  {peers.map((peer) => (
                    <MenuItem key={peer.staff_id} value={peer.staff_id}>
                      {peer.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </DialogContent>
            <DialogActions sx={{ m: 2 }}>
              <Button onClick={handleCloseModal} color="secondary">Cancel</Button>
              <Button
                variant="contained"
                color="primary"
                onClick={handleDelegate}
                data-cy="delegate-manager-button"
              >
                Delegate Manager
              </Button>
            </DialogActions>
          </Dialog>

          <SnackBarComponent
            showSnackbar={snackbar.showSnackbar}
            handleCloseSnackBar={handleCloseSnackBar}
            alertStatus={snackbar.alertStatus}
            snackbarMessage={snackbar.snackbarMessage}
          />

          <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>Delegated Manager ID</TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>Delegated Manager Name</TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>Date of Delegation</TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>Delegation Status</TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {delegationLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No delegation requests found
                    </TableCell>
                  </TableRow>
                ) : (
                  delegationLogs.map((log) => (
                    <TableRow key={log.delegate_manager_id}>
                      <TableCell>{log.delegate_manager_id}</TableCell>
                      <TableCell>{log.delegate_manager_name}</TableCell>
                      <TableCell>{new Date(log.date_of_delegation).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip
                          label={capitalize(log.status_of_delegation)}
                          color={
                            log.status_of_delegation === DelegationStatus.Accepted
                              ? "success"
                              : log.status_of_delegation === DelegationStatus.Rejected
                                ? "error"
                                : log.status_of_delegation === DelegationStatus.Pending
                                  ? "warning"
                                  : "default"
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outlined"
                          color="secondary"
                          onClick={() => handleCancelDelegation(log.delegate_manager_id)}
                          disabled={log.status_of_delegation !== DelegationStatus.Accepted}
                          data-cy="cancel-delegation-button"
                        >
                          Cancel
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Container >
  );
};

export default SendDelegation;
