import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
  TextField,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Button,
  Box,
  Stack,
  InputAdornment,
  OutlinedInput,
  Checkbox,
  ListItemText,
} from "@mui/material";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import { ApprovalStatus } from "../types/status";

interface FiltersProps {
  onApplyFilters: (filters: {
    startDate: Date | null;
    endDate: Date | null;
    department: string[];
    status: ApprovalStatus[];
    searchQuery: string;
    workStatus: string[];
  }) => void;
  onClearFilters: () => void;
}

export const Filters: React.FC<FiltersProps> = ({ onApplyFilters, onClearFilters }) => {
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [department, setDepartment] = useState<string[]>([]);
  const [status, setStatus] = useState<ApprovalStatus[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [workStatus, setWorkStatus] = useState<string[]>([]);

  // Update filters dynamically on search query change
  useEffect(() => {
    onApplyFilters({
      startDate,
      endDate,
      department,
      status,
      searchQuery,
      workStatus,
    });
  }, [searchQuery]); // Trigger filtering when searchQuery changes

  const handleApplyFilters = () => {
    onApplyFilters({
      startDate,
      endDate,
      department,
      status,
      searchQuery,
      workStatus,
    });
  };

  const handleClearFilters = () => {
    setStartDate(null);
    setEndDate(null);
    setDepartment([]);
    setStatus([]);
    setSearchQuery("");
    setWorkStatus([]);
    onClearFilters(); // Call parent-provided clear function
  };

  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        label="Search"
        variant="outlined"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search by Staff ID, Date, Reason, or Type"
        sx={{ marginBottom: 2 }}
      />

      <Box display="flex" flexWrap="wrap" gap={2} alignItems="center" padding={2} border={1} borderRadius={1} borderColor="grey.300">
        {/* Date Range Filter */}
        <Box display="flex" gap={2} alignItems="center" border={1} borderColor="grey.300" padding={1} borderRadius={1}>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            placeholderText="Start date"
            dateFormat="yyyy-MM-dd"
            customInput={
              <TextField
                variant="outlined"
                size="small"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <CalendarTodayIcon />
                    </InputAdornment>
                  ),
                }}
              />
            }
          />
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            placeholderText="End date"
            dateFormat="yyyy-MM-dd"
            customInput={
              <TextField
                variant="outlined"
                size="small"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <CalendarTodayIcon />
                    </InputAdornment>
                  ),
                }}
              />
            }
          />
        </Box>

        {/* Department Filter */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Department</InputLabel>
          <Select
            multiple
            value={department}
            onChange={(e) => setDepartment(e.target.value as string[])}
            input={<OutlinedInput label="Department" />}
            renderValue={(selected) => selected.join(", ")}
          >
            <MenuItem value="Sales">Sales</MenuItem>
            <MenuItem value="Consultancy">Consultancy</MenuItem>
            <MenuItem value="Systems Solutioning">Systems Solutioning</MenuItem>
            <MenuItem value="Engineering Operation">Engineering Operation</MenuItem>
            <MenuItem value="HR and Admin">HR and Admin</MenuItem>
            <MenuItem value="Finance and IT">Finance and IT</MenuItem>
          </Select>
        </FormControl>

        {/* Status Filter */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            multiple
            value={status}
            onChange={(e) => setStatus(e.target.value as ApprovalStatus[])}
            input={<OutlinedInput label="Status" />}
            renderValue={(selected) => selected.join(", ")}
          >
            {Object.values(ApprovalStatus).map((statusKey) => (
              <MenuItem key={statusKey} value={statusKey}>
                <Checkbox checked={status.includes(statusKey)} />
                <ListItemText primary={statusKey.replace(/^\w/, (c) => c.toUpperCase())} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Apply and Clear Filters Buttons */}
        <Box display="flex" gap={1}>
          <Button variant="contained" color="primary" onClick={handleApplyFilters}>
            Apply Filters
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleClearFilters}>
            Clear Filters
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default Filters;
