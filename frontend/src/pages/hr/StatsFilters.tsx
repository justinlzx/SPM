import { useState } from "react";
import Button from "@mui/material/Button";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import {
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  MenuItem,
  Box,
} from "@mui/material";

export type TFilters = {
  department: string;
  date: Date;
};

type PropType = {
  userInfo: {
    department?: string;
  };
  action: (filters: TFilters) => void;
};

const formatDate = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1; // Months are zero-based
  const day = date.getDate();

  // Pad month and day with zero if needed
  const monthStr = month < 10 ? "0" + month : month;
  const dayStr = day < 10 ? "0" + day : day;

  return `${year}-${monthStr}-${dayStr}`;
};

export const StatsFilters = ({ userInfo, action }: PropType) => {
  const [department, setDepartment] = useState(userInfo.department || "");
  const [date, setDate] = useState(new Date());
  const [error, setError] = useState("");

  const handleDateChange = (value: string) => {
    const date = new Date(value);
    setDate(date);
  };

  const handleClearFilters = () => {
    setDepartment(userInfo.department || "");
    setDate(new Date());
  };

  return (
    <div className="p-20">
      <div className="flex flex-col items-center">
        <Box className="flex gap-4 mb-4">
          {/* Department Filter */}
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Department</InputLabel>
            <Select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              input={<OutlinedInput label="Department" />}
            >
              <MenuItem value="Sales">Sales</MenuItem>
              <MenuItem value="Consultancy">Consultancy</MenuItem>
              <MenuItem value="Solutioning">Solutioning</MenuItem>
              <MenuItem value="Engineering">Engineering</MenuItem>
              <MenuItem value="HR">HR</MenuItem>
              <MenuItem value="Finance">Finance</MenuItem>
              <MenuItem value="IT">IT</MenuItem>
              <MenuItem value="all">All</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <div className="flex justify-center">
          <div className="flex flex-col gap-2 p-4">
            <label className="mx-1 font-leagueSpartan-400">Select Date:</label>
            <input
              type="date"
              className="w-[180px] border border-neutral-300 font-leagueSpartan-400 rounded-lg"
              value={formatDate(date)}
              onChange={(e) => {
                handleDateChange(e.target.value);
              }}
            />
          </div>
        </div>
        {error && <p className="text-red-500">{error}</p>}
        <div className="grid grid-cols-2">
          <Button
            sx={{
              backgroundColor: "navy",
              color: "white",
            }}
            onClick={() =>
              action({
                department,
                date,
              })
            }
          >
            Go
          </Button>
          <Button
            sx={{
              backgroundColor: "lightGray",
              color: "white",
              marginLeft: "4px",
            }}
            onClick={handleClearFilters}
          >
            <RestartAltIcon />
          </Button>
          <div className="mt-2 text-gray-500 text-sm col-span-2 text-center">
            Press GO to search
          </div>
        </div>
      </div>
    </div>
  );
};
