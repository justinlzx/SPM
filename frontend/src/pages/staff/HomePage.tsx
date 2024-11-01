import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; 
import { UserContext } from '../../context/UserContextProvider';
import AddIcon from '@mui/icons-material/Add';
import { Button, Box, Container, Typography } from '@mui/material';
import DashboardCards from '../../common/DashboardCards';
import { DelegateButton } from '../manager/DelegateButton';
import { PersonalRequests }  from './PersonalRequests';

export const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  const storedUser = localStorage.getItem('user');
  const userName = storedUser
    ? storedUser.split('@')[0].split('.').map(part => part[0].toUpperCase() + part.slice(1).toLowerCase()).join(' ')
    : "Guest";

  const handleCreateApplication = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Container maxWidth="lg" sx={{ padding: 0 }}>
        <Typography variant="h4" sx={{ my: 4 }}>
          Welcome back, {userName}
        </Typography>
        <DashboardCards />
        
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleCreateApplication('/create-request')}
        >
          Create a WFH Request
        </Button>
        <DelegateButton />
        {user && <PersonalRequests />} {/* Only render PersonalRequests if user is defined */}
      </Container>
    </Box>
  );
};

export default HomePage;

