import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TableSortLabel,
  Typography,
  CircularProgress,
  Box,
} from "@mui/material";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type Request = {
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  update_datetime: string;
  approval_status: string;
  reason_description: string;
  batch_id: string | null;
};

type Employee = {
  staff_id: number;
  staff_fname: string;
  staff_lname: string;
  position: string;
  country: string;
  email: string;
  dept: string;
};

type Order = 'asc' | 'desc';

const PendingRequests = () => {
  const [requests, setRequests] = useState<Request[]>([]);
  const [employees, setEmployees] = useState<{ [key: number]: Employee }>({});
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState<Order>('asc');
  const [orderBy, setOrderBy] = useState<keyof Request | keyof Employee | 'full_name'>('requester_staff_id'); // Default sorting by staff ID

  useEffect(() => {
    // Fetch the pending requests
    const fetchRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view`);
        setRequests(response.data);
        setLoading(false);

        // Fetch employee names for each requester
        await fetchEmployeeNames(response.data);
      } catch (error) {
        console.error("Error fetching requests:", error);
        setLoading(false);
      }
    };

    fetchRequests();
  }, []);

  // Function to fetch employee details for each requester
  const fetchEmployeeNames = async (requests: Request[]) => {
    const employeePromises = requests.map(async (request) => {
      try {
        const response = await axios.get(`${BACKEND_URL}/employee/${request.requester_staff_id}`);
        const employeeData: Employee = {
          staff_id: response.data.staff_id,
          staff_fname: response.data.staff_fname,
          staff_lname: response.data.staff_lname,
          position: response.data.position,
          country: response.data.country,
          email: response.data.email,
          dept: response.data.dept,
        };
        return employeeData;
      } catch (error) {
        console.error(`Error fetching employee details for ID: ${request.requester_staff_id}`, error);
        return null;
      }
    });

    // Wait for all employee data to be fetched
    const employeesData = await Promise.all(employeePromises);

    // Map employee data by staff_id for quick lookup
    const employeesMap: { [key: number]: Employee } = {};
    employeesData.forEach((employee) => {
      if (employee) {
        employeesMap[employee.staff_id] = employee;
      }
    });

    setEmployees(employeesMap); // Set the employee data in state
  };

  const handleSortRequest = (property: keyof Request | keyof Employee | 'full_name') => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedRequests = requests.slice().sort((a, b) => {
    if (orderBy === 'full_name') {
      const fullNameA = employees[a.requester_staff_id]
        ? `${employees[a.requester_staff_id].staff_fname} ${employees[a.requester_staff_id].staff_lname}`
        : 'Not Available';
      const fullNameB = employees[b.requester_staff_id]
        ? `${employees[b.requester_staff_id].staff_fname} ${employees[b.requester_staff_id].staff_lname}`
        : 'Not Available';
      return order === 'asc'
        ? fullNameA.localeCompare(fullNameB)
        : fullNameB.localeCompare(fullNameA);
    } else if (orderBy === 'wfh_date') {
      const dateA = new Date(a.wfh_date).getTime();
      const dateB = new Date(b.wfh_date).getTime();
      return order === 'asc' ? dateA - dateB : dateB - dateA;
    } else if (orderBy in employees) {
      const empA = employees[a.requester_staff_id]
        ? employees[a.requester_staff_id][orderBy as keyof Employee]
        : 'Not Available';
      const empB = employees[b.requester_staff_id]
        ? employees[b.requester_staff_id][orderBy as keyof Employee]
        : 'Not Available';
  
      // Check if both values are strings, use localeCompare, otherwise, handle as numbers
      if (typeof empA === 'string' && typeof empB === 'string') {
        return order === 'asc'
          ? empA.localeCompare(empB)
          : empB.localeCompare(empA);
      } else {
        return order === 'asc'
          ? (empA as number) - (empB as number)
          : (empB as number) - (empA as number);
      }
    } else {
      const aValue = a[orderBy as keyof Request];
      const bValue = b[orderBy as keyof Request];
  
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return order === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return order === 'asc' ? (aValue as number) - (bValue as number) : (bValue as number) - (aValue as number);
      }
    }
  });
  

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container>
      <Typography variant="h4" gutterBottom align="center" sx={{ marginTop: 4 }}>
        Pending Requests
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'requester_staff_id'}
                  direction={orderBy === 'requester_staff_id' ? order : 'asc'}
                  onClick={() => handleSortRequest('requester_staff_id')}
                >
                  Requester Staff ID
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'full_name'}
                  direction={orderBy === 'full_name' ? order : 'asc'}
                  onClick={() => handleSortRequest('full_name')}
                >
                  Full Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'position'}
                  direction={orderBy === 'position' ? order : 'asc'}
                  onClick={() => handleSortRequest('position')}
                >
                  Position
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'dept'}
                  direction={orderBy === 'dept' ? order : 'asc'}
                  onClick={() => handleSortRequest('dept')}
                >
                  Dept
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'country'}
                  direction={orderBy === 'country' ? order : 'asc'}
                  onClick={() => handleSortRequest('country')}
                >
                  Country
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'email'}
                  direction={orderBy === 'email' ? order : 'asc'}
                  onClick={() => handleSortRequest('email')}
                >
                  Email
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'wfh_date'}
                  direction={orderBy === 'wfh_date' ? order : 'asc'}
                  onClick={() => handleSortRequest('wfh_date')}
                >
                  WFH Date
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'wfh_type'}
                  direction={orderBy === 'wfh_type' ? order : 'asc'}
                  onClick={() => handleSortRequest('wfh_type')}
                >
                  WFH Type
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'approval_status'}
                  direction={orderBy === 'approval_status' ? order : 'asc'}
                  onClick={() => handleSortRequest('approval_status')}
                >
                  Approval Status
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedRequests.map((request) => (
              <TableRow key={request.arrangement_id}>
                <TableCell>{request.requester_staff_id}</TableCell>
                <TableCell>
                  {employees[request.requester_staff_id]
                    ? `${employees[request.requester_staff_id].staff_fname} ${employees[request.requester_staff_id].staff_lname}`
                    : 'Not Available'}
                </TableCell>
                <TableCell>{employees[request.requester_staff_id]?.position || 'Not Available'}</TableCell>
                <TableCell>{employees[request.requester_staff_id]?.dept || 'Not Available'}</TableCell>
                <TableCell>{employees[request.requester_staff_id]?.country || 'Not Available'}</TableCell>
                <TableCell>{employees[request.requester_staff_id]?.email || 'Not Available'}</TableCell>
                <TableCell>{request.wfh_date}</TableCell>
                <TableCell>{request.wfh_type}</TableCell>
                <TableCell>{request.approval_status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default PendingRequests;
