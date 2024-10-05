import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom'; 
import { UserContext } from '../../context/UserContextProvider';
import AddIcon from '@mui/icons-material/Add';
import { Button, Box, Toolbar, Container, Typography } from '@mui/material';
import DashboardCards from '../../components/staffView/DashboardCards';
import { RequestList } from '../../pages/team/RequestList';

type Request = {
  id: number;
  wfh_type: string;
  startDate: Date;
  endDate: Date;
  status: string;
};

export const HomePage = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const storedUser = localStorage.getItem('user');
  const userName = storedUser 
    ? storedUser.split('@')[0].split('.').map(part => part[0].toUpperCase() + part.slice(1).toLowerCase()).join(' ')
    : "Guest";

  const handleCreateApplication = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ flexGrow: 1}}>
      <Container maxWidth="lg" sx={{ padding: 0 }}>
      <Typography variant="h4" sx={{ my: 4 }}>
        Welcome back, {userName}
      </Typography>
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
        <RequestList />
      </Container>
    </Box>
  );
};

export default HomePage;