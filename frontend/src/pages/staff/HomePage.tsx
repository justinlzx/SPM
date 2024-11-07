import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UserContext } from "../../context/UserContextProvider";
import AddIcon from "@mui/icons-material/Add";
import { Button, Box, Container, Typography } from "@mui/material";
import DashboardCards from "../../common/DashboardCards";
import { DelegateButton } from "../manager/DelegateButton";
import PersonalRequests from "./PersonalRequests";
import axios from "axios";
import { ApprovalStatus } from "../../types/status";
import { TWFHRequest } from "../../types/requests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  const [approvedCount, setApprovedCount] = useState<number>(0);
  const [approvedThisMonth, setApprovedThisMonth] = useState<number>(0);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${user?.id}`
        );

        const allRequests: TWFHRequest[] = response.data.data;

        // Calculate approved requests count
        const approvedRequestsCount = allRequests.filter(
          (request) =>
            request.current_approval_status === ApprovalStatus.Approved
        ).length;
        setApprovedCount(approvedRequestsCount);

        // Calculate approved WFH days for the current month
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();

        const approvedThisMonthCount = allRequests.filter((request) => {
          const requestDate = new Date(request.wfh_date);
          return (
            request.current_approval_status === ApprovalStatus.Approved &&
            requestDate.getMonth() === currentMonth &&
            requestDate.getFullYear() === currentYear
          );
        }).length;

        setApprovedThisMonth(approvedThisMonthCount);
      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      }
    };

    if (user) {
      fetchRequests();
    }
  }, [user]);

  const storedUser = localStorage.getItem("user");
  const userName = storedUser
    ? storedUser
      .split("@")[0]
      .split(".")
      .map((part) => part[0].toUpperCase() + part.slice(1).toLowerCase())
      .join(" ")
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
        <DashboardCards
          wfhDaysTaken={approvedThisMonth}
          approvedRequests={approvedCount}
          importantMessage="Remember to submit your WFH requests a day in advance."
        />

        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleCreateApplication("/create-request")}
          data-cy="home-page-create-request-button"
        >
          Create a WFH Request
        </Button>
        {(user?.role === 2 ||
          (user?.role === 1 && user?.position === "Director")) && (
            <DelegateButton data-cy="home-page-delegate-button" />
          )}
        <Typography variant="h5" sx={{ mt: 4 }}>
          Your Requests
        </Typography>
        <PersonalRequests />
      </Container>
    </Box>
  );
};

export default HomePage;
