import axios from "axios";
import { useContext, useEffect, useState } from "react";
import { TWFHRequest } from "../../types/requests";
import {
  Box,
  CircularProgress,
  Container,
  Divider,
  Typography,
} from "@mui/material";
import { StatsFilters, TFilters } from "./StatsFilters";
import { UserContext } from "../../context/UserContextProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const Statistics = () => {
  useEffect(() => {
    const getWFHRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`);
        // console.log(response.data);
      } catch (error) {
        console.error(error);
      }
    };
    getWFHRequests();
    setIsLoading(false);
  }, []);

  const { user } = useContext(UserContext);

  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilters>({
    status: "approved",
    department: "",
    dates: {
      start: new Date(),
      end: new Date(),
    },
  });

  const handleFilterChange = (filters: TFilters) => {
    setFilters(filters);
  };

  if (isLoading) {
    return (
      <div
        style={{ display: "flex", justifyContent: "center", padding: "2rem" }}
      >
        <CircularProgress />
      </div>
    );
  }

  console.log(filters);
  console.log(user);

  return (
    <Container>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        View Organisation Statistics
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <StatsFilters
        userInfo={{ department: user?.dept }}
        action={(filterValues) => handleFilterChange(filterValues)}
      />
    </Container>
  );
};
