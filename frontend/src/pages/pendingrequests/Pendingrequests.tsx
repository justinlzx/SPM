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

type Request = {
  requester_staff_id: number;
  wfh_date: string; // Date is stored as a string
  wfh_type: string;
  arrangement_id: number;
  update_datetime: string;
  approval_status: string;
  reason_description: string;
  batch_id: string | null;
};

type Order = 'asc' | 'desc';

const PendingRequests = () => {
  const [requests, setRequests] = useState<Request[]>([]);
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState<Order>('asc');
  const [orderBy, setOrderBy] = useState<keyof Request>('requester_staff_id'); // Default sorting by staff ID

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view`);
        setRequests(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching requests:", error);
        setLoading(false);
      }
    };

    fetchRequests();
  }, []);

  const handleSortRequest = (property: keyof Request) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedRequests = requests.slice().sort((a, b) => {
    const aValue = a[orderBy];
    const bValue = b[orderBy];

    if (orderBy === 'wfh_date') {
      // Convert date strings to Date objects for accurate comparison
      const dateA = new Date(a.wfh_date).getTime();
      const dateB = new Date(b.wfh_date).getTime();
      return order === 'asc' ? dateA - dateB : dateB - dateA;
    } else {
      // For other fields, just compare normally
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
