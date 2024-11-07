import React, { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { PendingRequests } from "../team/PendingRequests";
import { Container } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";

export const ReviewRequests: React.FC = () => {
  const { user } = useContext(UserContext);
  if (!user) return <p>Please log in to view requests.</p>;
  const navigate = useNavigate();
  if (!user) {
    navigate("/login");
  }

  return (
    <Container>
      <PendingRequests />
    </Container>
  );
};
