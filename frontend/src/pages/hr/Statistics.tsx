import axios from "axios";
import { useEffect, useState } from "react";
import { TWFHRequest } from "../../types/requests";
import {
  Box,
  CircularProgress,
  Container,
  Divider,
  Typography,
} from "@mui/material";
import { set } from "react-datepicker/dist/date_utils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TFilter = {
  status: string;
  department: string;
  date: string;
};

export const Statistics = () => {
  useEffect(() => {
    const getWFHRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`);
        console.log(response.data);
      } catch (error) {
        console.error(error);
      }
    };
    getWFHRequests();
    setIsLoading(false);
  }, []);

  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilter>({
    status: "approved",
    department: "",
    date: "",
  });

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
    </Container>
  );
};
