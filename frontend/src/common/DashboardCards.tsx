import React from "react";
import { Box, Card, CardContent, Typography } from "@mui/material";

interface DashboardCardsProps {
  wfhDaysTaken: number;
  approvedRequests: number;
  importantMessage: string;
}

export const DashboardCards: React.FC<DashboardCardsProps> = ({
  wfhDaysTaken,
  approvedRequests,
  importantMessage,
}) => {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "repeat(1, 1fr)", sm: "repeat(2, 1fr)", md: "repeat(3, 1fr)" },
        gap: 2,
        mb: 2,
      }}
    >
      {/* WFH Days Taken Card */}
      <Card sx={{ border: "1px solid lightgrey", borderRadius: "8px" }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            WFH Days Taken This Month
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {wfhDaysTaken}
          </Typography>
        </CardContent>
      </Card>

      {/* Approved Requests Card */}
      <Card sx={{ border: "1px solid lightgrey", borderRadius: "8px" }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            Approved Requests
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {approvedRequests}
          </Typography>
        </CardContent>
      </Card>

      {/* Important Message Card */}
      <Card sx={{ border: "1px solid lightgrey", borderRadius: "8px" }}>
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
