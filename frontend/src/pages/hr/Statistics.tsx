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

const CHART_COLOURS = ["#aad6ec", "#0f1056", "#DFEBF6", "#81b1ce", "#000080"];

export const Statistics = () => {
  const { user } = useContext(UserContext);

  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<number[]>([]);
  const [filters, setFilters] = useState<TFilters>({
    department: user?.dept || "all",
    date: new Date(),
  });

  const handleFilterChange = (filters: TFilters) => {
    setFilters(filters);
  };

  useEffect(() => {
    setIsLoading(true);

    const countArrangements = async (arrangements: TWFHRequest[]) => {
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

        if (arrangement.reason_description.slice(0,3) === "OOO") {
          counts.onLeave++;
        }
      });

      const totalEmployees = await getTotalEmployees();
      const inOffice =
        totalEmployees -
        (counts.onLeave + counts.wfh_full + counts.wfh_am + counts.wfh_pm);

      return [
        counts.onLeave,
        counts.wfh_full,
        counts.wfh_am,
        counts.wfh_pm,
        inOffice,
      ];
    };
    const getWFHRequests = async () => {
      const params = {
        department:
          filters.department === "all" ? undefined : filters.department,
        current_approval_status: ["APPROVED"],
        start_date: new Date(filters.date.toISOString().split("T")[0]), // strip the time away and convert all to 0s then convert back to a date object
        end_date: new Date(filters.date.toISOString().split("T")[0]),
      };

      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements`, {
          params,
        });
        const arrangementData = await countArrangements(response.data.data);
        setData(arrangementData);
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    const getTotalEmployees = async () => {
      const response = await axios.get(`${BACKEND_URL}/employees`, {
        params: {
          department:
            filters.department !== "all" ? filters.department : undefined,
        },
      });

      return response.data.length;
    };

    getWFHRequests();
  }, [filters, BACKEND_URL]);

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
            {data.slice(0, 3).reduce((count, val) => count + val, 0) === 0 ? (
              <Box className="h-full flex justify-center items-center">
                {isLoading ? (
                  <CircularProgress />
                ) : (
                  <Typography variant="h6" align="center">
                    No arrangements made for the selected date
                  </Typography>
                )}
              </Box>
            ) : (
              <Chart
                data={data}
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
            )}
          </Box>
        </Box>
      </Box>
    </Container>
  );
};
