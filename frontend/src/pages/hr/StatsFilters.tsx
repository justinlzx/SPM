import { Box } from "@mui/material";
import { useState } from "react";
import { DatePicker } from "./DatePicker";

export const StatsFilters = () => {
  const [dates, setDates] = useState({
    start: new Date(),
    end: new Date(),
  });
  const [department, setDepartment] = useState("");

  return (
    <Box>
      <DatePicker action={(dateRange) => setDates(dateRange)} />
    </Box>
  );
};
