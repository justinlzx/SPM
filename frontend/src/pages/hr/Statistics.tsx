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
import { Chart } from "./chart/Chart";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const Statistics = () => {
  const { user } = useContext(UserContext);

  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilters>({
    status: "approved",
    department: "",
    date: new Date(),
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
            start_date: filters.date.toISOString().split("T")[0], // convert to datestring to suit backend input
            end_date: filters.date.toISOString().split("T")[0],
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

  const TOTAL_EMPLOYEES = 500;

  const countArrangements = (arrangements: TWFHRequest[]) => {
    let counts = {
      onLeave: 0,
      wfh_full: 0,
      wfh_am: 0,
      wfh_pm: 0,
    };

    arrangements.forEach((arrangement) => {
      switch (arrangement.wfh_type) {
        case "WFH (Full Day)":
          counts.wfh_full++;
          break;
        case "WFH (AM)":
          counts.wfh_am++;
          break;
        case "WFH (PM)":
          counts.wfh_pm++;
          break;
      }

      if (arrangement.reason_description === "OOO") {
        counts.onLeave++;
      }
    });

    const inOffice =
      TOTAL_EMPLOYEES -
      (counts.onLeave + counts.wfh_full + counts.wfh_am + counts.wfh_pm);

    return [
      counts.onLeave,
      counts.wfh_full,
      counts.wfh_am,
      counts.wfh_pm,
      inOffice,
    ];
  };

  const arrangementData = countArrangements(data);

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
        <Box className="w-full border-grey border-[1px] rounded-lg p-8 flex justify-center">
          <Chart data={arrangementData} />
        </Box>
      </Box>
    </Container>
  );
};
