import React, { useEffect, useState, useContext } from "react";
import { PendingRequests, TWFHRequest } from "../team/PendingRequests";
import axios from "axios";
import { Container } from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { Filters } from "../../common/Filters";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ReviewRequests: React.FC = () => {
  const { user } = useContext(UserContext);
  const [requests, setRequests] = useState<TWFHRequest[]>([]);

  if (!user) return <p>Please log in to view requests.</p>;

  return (
    <Container>
      <PendingRequests />
    </Container>
  );
};
