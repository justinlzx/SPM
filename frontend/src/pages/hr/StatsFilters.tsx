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
  status: string;
  department: string;
  dates: {
    start: Date;
    end: Date;
  };
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
  const [status, setStatus] = useState("approved");
  const [dates, setDates] = useState({
    start: new Date(),
    end: new Date(),
  });
  const [error, setError] = useState("");

  const handleDateChange = (value: string, type: Date) => {
    const date = new Date(value);
    if (type === dates.start && date > dates.end) {
      setError("Start date cannot be after end date");
      return;
    } else if (type === dates.end && date < dates.start) {
      setError("End date cannot be before start date");
      return;
    } else {
      setError("");
    }

    if (type === dates.start) {
      setDates((prev) => ({
        ...prev,
        start: date,
      }));
    } else {
      setDates((prev) => ({
        ...prev,
        end: date,
      }));
    }
  };

  const handleClearFilters = () => {
    setDepartment(userInfo.department || "");
    setStatus("approved");
    setDates({
      start: new Date(),
      end: new Date(),
    });
  };

  const handleFixedDateSelect = (days: number) => {
    const newEnd = new Date(
      dates.end.getTime() - (days - 1) * 24 * 60 * 60 * 1000
    );
    setDates((prev) => ({
      ...prev,
      end: newEnd,
    }));
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
              <MenuItem value="Systems Solutioning">Solutioning</MenuItem>
              <MenuItem value="Engineering">Engineering</MenuItem>
              <MenuItem value="HR">HR</MenuItem>
              <MenuItem value="Finance">Finance</MenuItem>
              <MenuItem value="T">IT</MenuItem>
            </Select>
          </FormControl>

          {/* Status Filter */}
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              input={<OutlinedInput label="Status" />}
            >
              <MenuItem value="approved">Approved</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <div className="flex gap-2">
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(7)}
          >
            Last 7 days
          </button>
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(15)}
          >
            Last 15 days
          </button>
          <button
            className="p-2 px-3 font-leagueSpartan-400 text-orange border border-orange rounded-lg hover:bg-lightOrange"
            onClick={() => handleFixedDateSelect(30)}
          >
            Last 30 days
          </button>
        </div>
        <div className="flex justify-center">
          <div className="flex flex-col gap-2 p-4">
            <label className="mx-1 font-leagueSpartan-400">Start:</label>
            <input
              type="date"
              className="w-[180px] border border-neutral-300 font-leagueSpartan-400 rounded-lg"
              value={formatDate(dates.start)}
              onChange={(e) => {
                handleDateChange(e.target.value, dates.start);
              }}
            />
          </div>
          <div className="flex flex-col gap-2 p-4">
            <label className="mx-1 font-leagueSpartan-400">End:</label>
            <input
              type="date"
              className="w-[180px] border border-neutral-300 font-leagueSpartan-400 rounded-lg"
              value={formatDate(dates.end)}
              onChange={(e) => {
                handleDateChange(e.target.value, dates.end);
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
                status: status,
                department: department,
                dates: dates,
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
