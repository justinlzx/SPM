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
  Button,
  ButtonGroup,
  TablePagination,
  Collapse,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
  List,
  ListItem,
  Tooltip,
  Chip,
} from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { TEmployee } from "../../hooks/employee/employee.utils";
import { ApprovalStatus } from "../../types/approvalStatus";
import { TWFHRequest } from "../../types/requests";
import { UserContext } from "../../context/UserContextProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type TAction = "approve" | "reject" ;


type TArrangementByEmployee = {
  employee: TEmployee;
  pending_arrangements: TWFHRequest[];
};

// Define Status Action Mapping
export const STATUS_ACTION_MAPPING = {
  [ApprovalStatus.PendingApproval]: {
    approve: ApprovalStatus.Approved,
    reject: ApprovalStatus.Rejected,
    cancel: ApprovalStatus.Cancelled,
  },
  [ApprovalStatus.Approved]: {
    withdraw: ApprovalStatus.PendingWithdrawal,
  },
  [ApprovalStatus.PendingWithdrawal]: {
    approve: ApprovalStatus.Withdrawn,
    reject: ApprovalStatus.Approved,
  },
  [ApprovalStatus.Rejected]: {},
  [ApprovalStatus.Withdrawn]: {},
};

export const PendingRequests = () => {
  const [actionRequests, setActionRequests] = useState<TArrangementByEmployee[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  useEffect(() => {
    const fetchPendingRequestsFromSubordinates = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}`
        );
        const pendingRequests = response.data.data;
        const validRequests = pendingRequests.filter(
          (request: TWFHRequest) => request.requester_staff_id
        );

        setActionRequests(validRequests);
      } catch (error) {
        console.error("Failed to fetch subordinates' requests:", error);
      }
    };
    fetchPendingRequestsFromSubordinates();
  }, [user, userId]);

  const handleRequestAction = async (
    action: TAction,
    arrangement_id: number,
    reason_description: string,
    current_approval_status: ApprovalStatus
  ) => {
    // Get the next status based on the current status and action
    const statusActions = STATUS_ACTION_MAPPING[current_approval_status as keyof typeof STATUS_ACTION_MAPPING];
    const nextStatus = (statusActions as Record<TAction, ApprovalStatus>)?.[action];
  
    // If the action is not allowed for the current status, log a warning and exit
    if (!nextStatus) {
      console.warn(`Action '${action}' is not allowed for status '${current_approval_status}'`);
      return;
    }
  
    try {
      // Prepare form data for the request
      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason_description", reason_description);
      formData.append("approving_officer", userId?.toString() || "");
      formData.append("current_approval_status", nextStatus); // Convert nextStatus to string if needed
  
      // Send the request to update the arrangement status
      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
  
      console.log(`Request '${action}' successfully updated to status '${nextStatus}'`);
      // Optionally, you may want to refresh the data here to reflect the new status
    } catch (error) {
      console.error(`Error performing action '${action}':`, error);
    }
  };
  
  

  return (
    <>
      <Typography
        variant="h4"
        gutterBottom
        align="left"
        sx={{ marginTop: 4 }}
      >
        Action Required
      </Typography>
      <TableContainer
        component={Paper}
        sx={{ marginTop: 3, textAlign: "center" }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Department</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Position</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Email</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Pending</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {actionRequests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No pending requests
                </TableCell>
              </TableRow>
            ) : (
              actionRequests.map((request) => (
                <EmployeeRow
                  key={request.employee.staff_id}
                  request={request}
                  handleRequestAction={handleRequestAction}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={actionRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) =>
          setRowsPerPage(parseInt(event.target.value, 10))
        }
      />
    </>
  );
};



const EmployeeRow = ({ request, handleRequestAction }: TEmployeeRow) => {
  const { employee } = request;

  // If employee data is missing, display a placeholder row
  if (!employee) {
    return (
      <TableRow>
        <TableCell colSpan={7} align="center">
          Employee data unavailable
        </TableCell>
      </TableRow>
    );
  }

  const { staff_id, staff_fname, staff_lname, dept, position, email } = employee;

  const arrangements = request.pending_arrangements.filter(
    (arrangement) =>
      arrangement.current_approval_status === ApprovalStatus.PendingApproval ||
      arrangement.current_approval_status === ApprovalStatus.PendingWithdrawal
  );

  const [isCollapsed, setIsCollapsed] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const handleDialogOpen = (documents: string[]) => {
    setDialogOpen(true);
    setDocuments(documents);
  };

  return (
    <>
      <TableRow key={staff_id}>
        {/* rest of the code remains unchanged */}
      </TableRow>
      <TableRow>
        {/* Collapse details remain unchanged */}
      </TableRow>
      <DocumentDialog
        isOpen={dialogOpen}
        documents={documents}
        onClose={() => setDialogOpen(false)}
      />
    </>
  );
};


type TEmployeeRow = {
  request: TArrangementByEmployee;
  handleRequestAction: (
    action: TAction,
    arrangement_id: number,
    reason_description: string,
    approval_status: ApprovalStatus
  ) => Promise<void>;
};

type TDocumentDialog = {
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
};

const DocumentDialog = ({ isOpen, documents, onClose }: TDocumentDialog) => {
  return (
    <Dialog open={isOpen} onClose={onClose} fullWidth>
      <DialogTitle
        className="flex justify-between items-center"
        sx={{ paddingBottom: 0 }}
      >
        Supporting Documents
        <DialogActions>
          <Button onClick={onClose}>
            <CloseIcon />
          </Button>
        </DialogActions>
      </DialogTitle>
      <DialogContent>
        <List>
          {documents.map((document, idx) => (
            <ListItem key={document}>
              {idx + 1}.
              <Link
                href={document}
                target="_blank"
                rel="noopener noreferrer"
                className="ps-2"
              >
                Click to View...
              </Link>
            </ListItem>
          ))}
        </List>
      </DialogContent>
    </Dialog>
  );
};
