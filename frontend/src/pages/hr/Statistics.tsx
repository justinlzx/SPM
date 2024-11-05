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

  useEffect(() => {
    const getWFHRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`, {
          params: {
            department: filters.department,
            status: filters.status,
            start_date: filters.dates.start.toISOString().split("T")[0], // convert to datestring to suit backend input
            end_date: filters.dates.end.toISOString().split("T")[0],
          },
        });
        console.log(response.data.data);
        setData(response.data.data);
      } catch (error) {
        console.error(error);
      }
    };
    getWFHRequests();
    setIsLoading(false);
  }, [filters, BACKEND_URL]);

  if (isLoading) {
    return (
      <div
        style={{ display: "flex", justifyContent: "center", padding: "2rem" }}
      >
        <CircularProgress />
      </div>
    );
  }

  return (
    <Container>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        View Organisation Statistics
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <Box className="flex gap-4 grid-cols-2">
        <StatsFilters
          userInfo={{ department: user?.dept }}
          action={(filterValues) => handleFilterChange(filterValues)}
        />
      </Box>
    </Container>
  );
};
