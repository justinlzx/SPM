import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import {
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material'; 
import { SnackBarComponent, AlertStatus } from '../../common/SnackBar';
import { UserContext } from '../../context/UserContextProvider';

interface Peer {
  staff_id: string;
  name: string;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const NominateManager: React.FC = () => {
  const { user } = useContext(UserContext);
  const userId = user!.id;
  const [peers, setPeers] = useState<Peer[]>([]);
  const [selectedPeer, setSelectedPeer] = useState(''); // Set default to an empty string
  const [snackbar, setSnackbar] = useState({
    showSnackbar: false,
    snackbarMessage: '',
    alertStatus: AlertStatus.Info,
  });
  const [openModal, setOpenModal] = useState(false);

  useEffect(() => {
    const fetchPeers = async () => {
      if (userId) {
        try {
          const response = await axios.get(`${BACKEND_URL}/employees/manager/peermanager/${userId}`);
          const peers= response.data.peer_employees;
          console.log(peers);
          setPeers(peers.map((peer: any) => ({
            staff_id: peer.staff_id,
            name: `${peer.staff_fname} ${peer.staff_lname}`,
          })));
        } catch (error) {
          console.error('Error fetching peers:', error);
          handleSnackbar(AlertStatus.Error, 'Failed to load peers.');
        }
      }
    };

    fetchPeers();
  }, [user]);

  const handlePeerSelect = (event: SelectChangeEvent<string>) => {
    setSelectedPeer(event.target.value); // This is guaranteed to be a string or '' based on the Select
  };

  const handleNominateManager = async () => {
    // Commented out until the backend is ready
    // try {
    //   await axios.put(`${BACKEND_URL}/employees/manager/employees/${selectedPeer}`);
    //   handleSnackbar(AlertStatus.Success, 'Peer successfully nominated as manager!');
    // } catch (error) {
    //   console.error('Error nominating peer:', error);
    //   handleSnackbar(AlertStatus.Error, 'Failed to nominate peer as manager');
    // }

    handleSnackbar(AlertStatus.Success, 'Peer successfully nominated as manager! (mock response)');
    setOpenModal(false);
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
    <>
      <Button variant="contained" color="primary" onClick={handleOpenModal}>
        Nominate a Manager
      </Button>

      <Dialog open={openModal} onClose={handleCloseModal}>
        <DialogTitle>Nominate a Peer for Manager Responsibilities</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ my:2 }}>
            <InputLabel id="select-peer-label">Select Manager</InputLabel>
            <Select
              labelId="select-peer-label"
              label="Select Manager"  
              value={selectedPeer}  // Directly use selectedPeer without undefined checks
              onChange={handlePeerSelect}
              displayEmpty
            >
              {peers.map((peer) => (
                <MenuItem key={peer.staff_id} value={peer.staff_id}>
                  {peer.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ mx:2}}>
          <Button onClick={handleCloseModal} color="secondary">Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            disabled={!selectedPeer}  // Disable if no peer is selected
            onClick={handleNominateManager}
          >
            Nominate Manager
          </Button>
        </DialogActions>
      </Dialog>

      <SnackBarComponent
        showSnackbar={snackbar.showSnackbar}
        handleCloseSnackBar={handleCloseSnackBar}
        alertStatus={snackbar.alertStatus}
        snackbarMessage={snackbar.snackbarMessage}
      />
    </>
  );
};

export default NominateManager;