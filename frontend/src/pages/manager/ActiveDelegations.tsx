import React, { useContext, useEffect, useState } from "react";
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
  Typography,
  Chip,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { capitalize } from "../../utils/utils";
import { SnackBarComponent, AlertStatus } from "../../common/SnackBar"; // Adjust the import path as necessary

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

enum DelegationStatus {
  Accepted = "accepted",
  Pending = "pending",
  Rejected = "rejected",
}

type TDelegationRequest = {
  date_of_delegation: string;
  full_name: string;
  staff_id: number;
  delegate_manager_id: number;
  status_of_delegation: DelegationStatus;
};

export const ActiveDelegations = () => {
  const [activeDelegations, setActiveDelegations] = useState<TDelegationRequest[]>([]);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  // Snackbar state
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Success);

  // Fetch active delegations for the manager
  useEffect(() => {
    const fetchActiveDelegations = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/employees/manager/viewdelegations/${userId}`,
          {
            params: {
              status: "accepted",
            },
          }
        );
        const activeDelegationRequests: TDelegationRequest[] = response.data.active_delegations || [];
        console.log("Active delegations:", activeDelegationRequests);
        setActiveDelegations(activeDelegationRequests);
      } catch (error) {
        console.error("Failed to fetch active delegations:", error);
        setSnackbarMessage("Failed to load active delegations.");
        setAlertStatus(AlertStatus.Error);
        setShowSnackbar(true);
      }
    };
    fetchActiveDelegations();
  }, [user, userId]);

  const handleCloseSnackBar = () => {
    setShowSnackbar(false);
  };

  return (
    <Container>
      <Typography variant="h6" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Active Delegations
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Delegator Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Delegator Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Date of Delegation</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Delegation Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {activeDelegations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  No active delegations found
                </TableCell>
              </TableRow>
            ) : (
              activeDelegations.map((delegation) => {
                const { staff_id, full_name, date_of_delegation, status_of_delegation } = delegation;
                return (
                  <TableRow key={staff_id}>
                    <TableCell>{staff_id}</TableCell>
                    <TableCell>{full_name}</TableCell>
                    <TableCell>{new Date(date_of_delegation).toLocaleDateString()}</TableCell> {/* Date */}
                    <TableCell>
                      <Chip
                        label={capitalize(status_of_delegation)}
                        color={
                          status_of_delegation === DelegationStatus.Accepted
                            ? "success"
                            : "default"
                        }
                      />
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <SnackBarComponent
        showSnackbar={showSnackbar}
        handleCloseSnackBar={handleCloseSnackBar}
        alertStatus={alertStatus}
        snackbarMessage={snackbarMessage}
      />
    </Container>
  );
};

export default ActiveDelegations;
