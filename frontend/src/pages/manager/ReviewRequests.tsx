import React, { useEffect, useState, useContext } from 'react';
import { PendingRequests, TWFHRequest } from '../team/PendingRequests';
import axios from 'axios';
import { Container } from '@mui/material';
import { UserContext } from '../../context/UserContextProvider';
import { Filters } from '../../components/Filters';


const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ReviewRequests: React.FC = () => {
  const { user } = useContext(UserContext);
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<TWFHRequest[]>([]);

  useEffect(() => {
    const fetchRequests = async () => {
      if (!user) return;

      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${user.id}`,
          { params: { current_approval_status: 'pending' } }
        );

        setRequests(response.data.data);
        setFilteredRequests(response.data.data); // Initialize filteredRequests with the same data
      } catch (error) {
        console.error('Error fetching requests:', error);
      }
    };

    fetchRequests();
  }, [user]);

  // Handle applying filters from Filters component
  const handleApplyFilters = (filters: {
    startDate: Date | null;
    endDate: Date | null;
    wfhType: string;
    requestStatus: string[];
    wfhDuration: string;
  }) => {
    const updatedFilteredRequests = requests.filter((request) => {
      const requestDate = request.wfh_date ? new Date(request.wfh_date) : null;
      if (filters.startDate && requestDate && requestDate < filters.startDate) return false;
      if (filters.endDate && requestDate && requestDate > filters.endDate) return false;
      if (filters.wfhType && request.wfh_type !== filters.wfhType) return false;
      if (filters.requestStatus.length > 0 && !filters.requestStatus.includes(request.approval_status || '')) return false;
      return true;
    });

    setFilteredRequests(updatedFilteredRequests);
  };

  if (!user) return <p>Please log in to view requests.</p>;

  return (
    <Container>
      <Filters onApply={handleApplyFilters} />
      {/* PendingRequests component receives filteredRequests */}
      <PendingRequests />
    </Container>
  );
};
