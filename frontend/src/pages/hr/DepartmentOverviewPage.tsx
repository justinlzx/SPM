import { useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { UserContext } from "../../context/UserContextProvider";
import { Box, Divider, Typography } from "@mui/material";
import RequestHistory from "./RequestHistory";
import { Statistics } from "./Statistics";

export const DepartmentOverviewPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  return (
    <Box>
      <Typography
        variant="h3"
        gutterBottom
        align="center"
        sx={{ marginTop: 4 }}
      >
        Department Overview
      </Typography>

      <Statistics />

      <RequestHistory />
    </Box>
  );
};
