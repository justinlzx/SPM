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
} from '@mui/material';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import { SelectChangeEvent } from '@mui/material';
import { SnackBarComponent, AlertStatus } from '../../common/SnackBar';
import { UserContext } from '../../context/UserContextProvider';
import { capitalize } from "../../utils/utils";

interface Peer {
  staff_id: string;
  name: string;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

enum DelegationStatus {
  Accepted = "accepted",
  Pending = "pending",
  Rejected = "rejected",
}

type TDelegationLog = {
  manager_id: number;
  delegate_manager_id: number;
  delegate_manager_name: string;
  date_of_delegation: string;
  status_of_delegation: DelegationStatus;
};

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

  useEffect(() => {
    const fetchPeers = async () => {
      if (userId) {
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
        }
      }
    };

    fetchPeers();
  }, [user]);

  useEffect(() => {
    const fetchDelegationLogs = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/employees/manager/viewalldelegations/${userId}`
        );
        const sentDelegations: TDelegationLog[] = response.data.sent_delegations || [];
        setDelegationLogs(sentDelegations);
      } catch (error) {
        console.error("Failed to fetch delegation logs:", error);
        handleSnackbar(AlertStatus.Error, 'Failed to load delegation logs.');
      }
    };
    fetchDelegationLogs();
  }, [user, userId]);

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
        'You have an active or pending delegation request for this manager. You cannot send another one right now.'
      );
      return;
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/employees/manager/delegate/${userId}`, null, {
        params: {
          delegate_manager_id: selectedPeer,
        },
      });
      setDelegationLogs((prevLogs) => [
        ...prevLogs,
        {
          manager_id: response.data.manager_id,
          delegate_manager_id: response.data.delegate_manager_id,
          delegate_manager_name: peers.find((peer) => peer.staff_id === selectedPeer)?.name || "Unknown",
          date_of_delegation: response.data.date_of_delegation,
          status_of_delegation: response.data.status_of_delegation,
        }
      ]);
      handleSnackbar(AlertStatus.Success, 'Request to delegate peer manager sent');
    } catch (error) {
      console.error('Error delegating peer:', error);
      handleSnackbar(AlertStatus.Error, 'Failed to delegate peer as manager.');
    } finally {
      setOpenModal(false);
    }
  };

  const handleCancelDelegation = async (delegateManagerId: number) => {
    try {
      await axios.put(`${BACKEND_URL}/employees/manager/undelegate/${userId}`, {
        params: { delegate_manager_id: delegateManagerId },
      });
      setDelegationLogs((prevLogs) => prevLogs.filter(log => log.delegate_manager_id !== delegateManagerId));
      handleSnackbar(AlertStatus.Success, 'Delegation canceled successfully.');
    } catch (error) {
      console.error('Error canceling delegation:', error);
      handleSnackbar(AlertStatus.Error, 'Failed to cancel delegation.');
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
      <Button variant="outlined" color="primary" onClick={handleOpenModal}>
        Delegate a Manager
      </Button>
    </Box>


      <Typography variant="h6">Sent Delegations</Typography>
      <Dialog open={openModal} onClose={handleCloseModal}>
        <DialogTitle>Delegate a Peer for Manager Responsibilities</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ my: 2 }}>
            <InputLabel id="select-peer-label">Select Manager</InputLabel>
            <Select
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

      {/* Sent Delegations Table */}
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
                      variant="outlined"
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
    </Container>
  );
};

export default SendDelegation;

interface SeePeerManagerButtonProps {
  onClick: () => void;
}

export const SeePeerManagerButton: React.FC<SeePeerManagerButtonProps> = ({ onClick }) => (
  <Button variant="outlined" color="primary" onClick={onClick}>
    Delegate a Manager
  </Button>
);

