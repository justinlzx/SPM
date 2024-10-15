import React, { useEffect, useState, useContext } from 'react';
import { PendingRequests } from '../team/PendingRequests'; // Ensure correct path
import axios from 'axios';
import { UserContext } from '../../context/UserContextProvider';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ReviewRequests: React.FC = () => {
  const { user } = useContext(UserContext); // Get user from context
  const [requests, setRequests] = useState([]); // Store pending requests

  // Fetch pending requests for manager’s subordinates
  useEffect(() => {
    const fetchRequests = async () => {
      if (!user) return; // Ensure user is available

      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${user.id}`,
          { params: { current_approval_status: 'pending' } }
        );

        setRequests(response.data.data); // Store fetched requests
      } catch (error) {
        console.error('Error fetching requests:', error);
      }
    };

    fetchRequests();
  }, [user]);

  if (!user) return <p>Please log in to view requests.</p>; // Handle no user case

  return (
    <div>
      <PendingRequests />
    </div>
  );
};
