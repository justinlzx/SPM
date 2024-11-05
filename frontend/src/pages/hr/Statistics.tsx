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

const CHART_COLOURS = ["#aad6ec", "#151269", "#0f1056", "#DFEBF6", "#81b1ce"];

export const Statistics = () => {
  const { user } = useContext(UserContext);

  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<TWFHRequest[]>([]);
  const [filters, setFilters] = useState<TFilters>({
    department: user?.dept || "all",
    date: new Date(),
  });

  const handleFilterChange = (filters: TFilters) => {
    setFilters(filters);
  };

  useEffect(() => {
    const getWFHRequests = async () => {
      const params = {
        department:
          filters.department === "all" ? undefined : filters.department,
        current_approval_status: ["APPROVED"],
        start_date: new Date(filters.date.toISOString().split("T")[0]), // strip the time away and convert all to 0s
        end_date: new Date(filters.date.toISOString().split("T")[0]),
      };

      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`, {
          params,
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

  const TOTAL_EMPLOYEES = 50;

  const countArrangements = (arrangements: TWFHRequest[]) => {
    let counts = {
      onLeave: 0,
      wfh_full: 0,
      wfh_am: 0,
      wfh_pm: 0,
    };

    arrangements.forEach((arrangement) => {
      switch (arrangement.wfh_type) {
        case "full":
          counts.wfh_full++;
          break;
        case "am":
          counts.wfh_am++;
          break;
        case "pm":
          counts.wfh_pm++;
          break;
      }

      if (arrangement.reason_description === "OOO") {
        counts.onLeave++;
      }
    });

    console.log(counts);

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

  console.log(arrangementData);

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
          <Box className="w-1/2">
            <Chart
              data={arrangementData}
              labels={[
                "On Leave",
                "WFH (Full Day)",
                "WFH (AM)",
                "WFH(PM)",
                "In Office",
              ]}
              backgroundColor={CHART_COLOURS}
              hoverBackgroundColor={CHART_COLOURS}
            />
          </Box>
        </Box>
      </Box>
    </Container>
  );
};
