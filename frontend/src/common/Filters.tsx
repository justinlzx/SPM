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
  InputAdornment,
  OutlinedInput,
  Checkbox,
  ListItemText,
} from "@mui/material";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import { ApprovalStatus } from "../types/status";

export type TFilters = {
  startDate: Date | null;
  endDate: Date | null;
  workStatus: ApprovalStatus[];
  searchQuery: string;
};

interface FiltersProps {
  onApplyFilters: (filters: TFilters) => void;
  onClearFilters: (filters: TFilters) => void;
  excludeDateFilter?: boolean;
  excludeStatusFilter?: boolean;
  excludeSearchFilter?: boolean;
  statusOptions?: ApprovalStatus[]; // New optional prop
}

export const Filters: React.FC<FiltersProps> = ({
  onApplyFilters,
  onClearFilters,
  excludeDateFilter = false,
  excludeStatusFilter = false,
  excludeSearchFilter = false,
  statusOptions = Object.values(ApprovalStatus), // Default to all statuses
}) => {
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [workStatus, setWorkStatus] = useState<ApprovalStatus[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  // Update filters dynamically on search query change
  useEffect(() => {
    if (!excludeSearchFilter) {
      onApplyFilters({
        startDate,
        endDate,
        workStatus,
        searchQuery,
      });
    }
  }, [searchQuery]); // Trigger filtering when searchQuery changes

  const handleApplyFilters = () => {
    onApplyFilters({
      startDate,
      endDate,
      workStatus,
      searchQuery,
    });
  };

  const handleClearFilters = () => {
    setStartDate(null);
    setEndDate(null);
    setWorkStatus([]);
    setSearchQuery("");
    onClearFilters({
      startDate,
      endDate,
      workStatus,
      searchQuery,
    }); // Call parent-provided clear function
  };

  return (
    <Box
      sx={{
        position: 'relative',
        zIndex: 1000, 
      }}
    >
      {!excludeSearchFilter && (
        <TextField
          fullWidth
          size="small"
          label="Search"
          variant="outlined"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by Staff ID, Date, Reason, or Type"
          sx={{ marginBottom: 2 }}
          data-cy="search-input" 
        />
      )}

      <Box
        display="flex"
        flexWrap="wrap"
        gap={2}
        alignItems="center"
        padding={2}
        border={1}
        borderRadius={1}
        borderColor="grey.300"
      >
        {!excludeDateFilter && (
          <Box
            display="flex"
            gap={2}
            alignItems="center"
            border={1}
            borderColor="grey.300"
            padding={1}
            borderRadius={1}
          >
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
                  data-cy="start-date-picker" // Added data-cy for start date picker
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
                      <>
                        <InputAdornment position="end"></InputAdornment>
                        <CalendarTodayIcon />
                      </>
                    ),
                  }}
                  data-cy="end-date-picker" // Added data-cy for end date picker
                />
              }
            />
          </Box>
        )}

        {!excludeStatusFilter && (
          <FormControl size="small" sx={{ minWidth: 150 }} data-cy="status-select">
            <InputLabel>Status</InputLabel>
            <Select
              multiple
              value={workStatus}
              onChange={(e) =>
                setWorkStatus(e.target.value as ApprovalStatus[])
              }
              input={<OutlinedInput label="Status" />}
              renderValue={(selected) =>
                selected.length > 1 ? `${selected.length} selected` : selected.join(", ")
              }
            >
              {statusOptions.map((statusKey) => (
                <MenuItem key={statusKey} value={statusKey}>
                  <Checkbox checked={workStatus.includes(statusKey)} />
                  <ListItemText
                    primary={statusKey.replace(/^\w/, (c) => c.toUpperCase())}
                  />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <Box display="flex" gap={1}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleApplyFilters}
            data-cy="apply-filters" // Added data-cy for apply filters button
          >
            Apply Filters
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            onClick={handleClearFilters}
            data-cy="clear-filters" // Added data-cy for clear filters button
          >
            Clear Filters
          </Button>
        </Box>
      </Box>
    </Box >
  );
};

export default Filters;
