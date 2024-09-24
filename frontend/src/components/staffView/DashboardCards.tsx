import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';

export const DashboardCards = () => {
  //hardcoded
  const wfhDaysTaken = 5; 
  const unreadNotifications = 3; 
  const importantMessage = "Remember to submit your WFH requests a day in advance."; 

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(1, 1fr)', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2, mb: 2 }}>
      {/* WFH Days Taken Card */}
      <Card sx={{ border: '1px solid lightgrey', borderRadius: '8px' }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            WFH Days Taken
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {wfhDaysTaken}
          </Typography>
        </CardContent>
      </Card>

      {/* Unread Inbox Notifications Card */}
      <Card sx={{ border: '1px solid lightgrey', borderRadius: '8px' }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            Unread Notifications
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {unreadNotifications}
          </Typography>
        </CardContent>
      </Card>

      {/* Important Message Card */}
      <Card sx={{ border: '1px solid lightgrey', borderRadius: '8px' }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            Important Notice
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {importantMessage}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DashboardCards;
