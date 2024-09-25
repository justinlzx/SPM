import React from 'react';
import { Box, Typography } from '@mui/material';

const Footer = () => {
  return (
    <Box sx={{ bgcolor: 'primary.main', color: 'white', p: 2, textAlign: 'center' }}>
      <Typography variant="body1">
        &copy; {new Date().getFullYear()} My App. All rights reserved.
      </Typography>
    </Box>
  );
};

export default Footer;