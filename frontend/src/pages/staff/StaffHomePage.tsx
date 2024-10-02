import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { RequestList } from '../../components/staffView/RequestList'; 
import { UserContext } from '../../context/UserContextProvider';
import AddIcon from '@mui/icons-material/Add';
import { Button, Box, Toolbar, Container } from '@mui/material';
import DashboardCards from '../../components/staffView/DashboardCards';

type Request = {
  id: number;
  wfh_type: string;
  startDate: Date;
  endDate: Date;
  status: string;
};

export const StaffHomePage = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  const handleCreateApplication = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ flexGrow: 1, p: 2 }}>
      <Container maxWidth="lg">
        <DashboardCards />
        <Button
          sx={{ mb: 2 }}
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleCreateApplication('/request')}
        >
          Create a WFH Request
        </Button>
        {/* <RequestList /> */}
      </Container>
    </Box>
  );
};

export default StaffHomePage;
