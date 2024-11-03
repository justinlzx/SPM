import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { TextField, Checkbox, FormControl, FormGroup, FormControlLabel, Select, MenuItem, InputLabel, Button, Box, Stack } from '@mui/material';

interface FiltersProps {
  onApplyFilters: (filters: {
    startDate: Date | null;
    endDate: Date | null;
    department: string[];
    status: string;
    name: string;
    approver: string;
    workStatus: string[];
  }) => void;
}

export const Filters: React.FC<FiltersProps> = ({ onApplyFilters }) => {
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [department, setDepartment] = useState<string[]>([]);
  const [status, setStatus] = useState("approved");
  const [name, setName] = useState("");
  const [approver, setApprover] = useState("");
  const [workStatus, setWorkStatus] = useState<string[]>([]);

  const handleApplyFilters = () => {
    onApplyFilters({
      startDate,
      endDate,
      department,
      status,
      name,
      approver,
      workStatus
    });
  };

  return (
    <Box padding={2}>
      <Stack direction="column" spacing={2}>
        {/* Date Range Filter */}
        <Box display="flex" alignItems="center">
          <label style={{ marginRight: '8px' }}>Start Date:</label>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            placeholderText="Select start date"
          />
        </Box>
        <Box display="flex" alignItems="center">
          <label style={{ marginRight: '8px' }}>End Date:</label>
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            placeholderText="Select end date"
          />
        </Box>

        {/* Department Filter */}
        <FormControl fullWidth>
          <InputLabel>Department</InputLabel>
          <Select
            multiple
            value={department}
            onChange={(e) => setDepartment(e.target.value as string[])}
          >
            <MenuItem value="Sales">Sales</MenuItem>
            <MenuItem value="HR">HR</MenuItem>
            <MenuItem value="Engineering">Engineering</MenuItem>
          </Select>
        </FormControl>

        {/* Status Filter */}
        <FormControl fullWidth>
          <InputLabel>Status</InputLabel>
          <Select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <MenuItem value="approved">Approved</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
          </Select>
        </FormControl>

        {/* Name Search */}
        <TextField
          fullWidth
          label="Search by Staff Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* Approver Search */}
        <TextField
          fullWidth
          label="Search by Approver Name"
          value={approver}
          onChange={(e) => setApprover(e.target.value)}
        />

        {/* WFH/OFFICE/LEAVE Filter */}
        <FormGroup row>
          {['WFH', 'OFFICE', 'LEAVE'].map((statusOption) => (
            <FormControlLabel
              key={statusOption}
              control={
                <Checkbox
                  checked={workStatus.includes(statusOption)}
                  onChange={(e) => {
                    const newStatus = e.target.checked
                      ? [...workStatus, statusOption]
                      : workStatus.filter((s) => s !== statusOption);
                    setWorkStatus(newStatus);
                  }}
                />
              }
              label={statusOption}
            />
          ))}
        </FormGroup>

        {/* Apply Filters Button */}
        <Button variant="contained" onClick={handleApplyFilters}>
          Apply Filters
        </Button>
      </Stack>
    </Box>
  );
};

export default Filters;
