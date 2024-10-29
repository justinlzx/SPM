import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  InputAdornment,
  IconButton,
} from "@mui/material";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";

export type FilterDatePickerProps = {
  label: string;
  selectedDate: Date | null;
  onChange: (date: Date | null) => void;
};

const FilterDatePicker = ({
  label,
  selectedDate,
  onChange,
}: FilterDatePickerProps) => {
  return (
    <DatePicker
      selected={selectedDate}
      onChange={onChange}
      dateFormat="dd/MM/yyyy"
      placeholderText={label}
      customInput={
        <TextField
          variant="outlined"
          sx={{ minWidth: 200 }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton>
                  <CalendarTodayIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      }
    />
  );
};

type TFilterProps = {
  onApply: (filters: {
    startDate: Date | null;
    endDate: Date | null;
    wfhType: string;
    requestStatus: string[];
    departments: string[];
    workType: string;
  }) => void;
};

export const Filters = ({ onApply }: TFilterProps) => {
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [wfhType, setWfhType] = useState<string>("");
  const [requestStatus, setRequestStatus] = useState<string[]>([]);
  const [sortByDate, setSortByDate] = useState<"asc" | "desc">("asc");
  const [error, setError] = useState<string | null>(null);

  const handleApplyFilters = () => {
    if (startDate && endDate && startDate > endDate) {
      setError("Start date cannot be after end date.");
      return;
    }
    setError(null);
    onApply({
      startDate,
      endDate,
      wfhType,
      requestStatus,
      departments: [],
      workType: "", 
    });
  };

  return (
    <div
      style={{
        marginBottom: "20px",
        padding: "10px",
        border: "1px solid #ccc",
        borderRadius: "8px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "nowrap",
          gap: "15px",
          alignItems: "center",
        }}
      >
        {/* Start Date Picker */}
        <FilterDatePicker
          label="Select Start Date"
          selectedDate={startDate}
          onChange={(date) => setStartDate(date)}
        />

        {/* End Date Picker */}
        <FilterDatePicker
          label="Select End Date"
          selectedDate={endDate}
          onChange={(date: Date | null) => setEndDate(date)}
        />

        {/* WFH Type Filter */}
        <FormControl variant="outlined" sx={{ minWidth: 150 }}>
          <InputLabel>WFH Type</InputLabel>
          <Select
            value={wfhType}
            onChange={(e) => setWfhType(e.target.value as string)}
            label="WFH Type"
          >
            <MenuItem value="Recurring">Recurring</MenuItem>
            <MenuItem value="AdHoc">AdHoc</MenuItem>
          </Select>
        </FormControl>

        {/* Request Status Filter */}
        <FormControl variant="outlined" sx={{ minWidth: 200 }}>
          <InputLabel>Request Status</InputLabel>
          <Select
            multiple
            value={requestStatus}
            onChange={(e) => setRequestStatus(e.target.value as string[])}
            label="Request Status"
            renderValue={(selected) => (selected as string[]).join(", ")}
          >
            <MenuItem value="Pending Approval">Pending Approval</MenuItem>
            <MenuItem value="Pending Withdrawal">Pending Withdrawal</MenuItem>
            <MenuItem value="Approved">Approved</MenuItem>
            <MenuItem value="Rejected">Rejected</MenuItem>
          </Select>
        </FormControl>

        {/* Sort By Date */}
        <FormControl variant="outlined" sx={{ minWidth: 120 }}>
          <InputLabel>Sort by</InputLabel>
          <Select
            value={wfhType}
            onChange={(e) => setSortByDate(e.target.value as "asc" | "desc")}
            label="Sort By Date"
          >
            <MenuItem value="asc">Ascending</MenuItem>
            <MenuItem value="desc">Descending</MenuItem>
          </Select>
        </FormControl>

        {/* Apply Button */}
        <Button
          variant="contained"
          color="primary"
          onClick={handleApplyFilters}
          sx={{ height: "fit-content" }}
        >
          Apply
        </Button>
      </div>
      {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}
    </div>
  );
};

export default Filters;
