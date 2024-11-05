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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tooltip,
  Box,
  Link,
  List,
  ListItem,
} from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { Filters } from "../../common/Filters";
import { fetchEmployeeByStaffId } from "../../hooks/employee/employee.utils";
import {
  ApprovalStatus,
  Action,
  STATUS_ACTION_MAPPING,
} from "../../types/status";
import { UserContext } from "../../context/UserContextProvider";
import { SnackBarComponent, AlertStatus } from "../../common/SnackBar";
import { LoadingSpinner } from "../../common/LoadingSpinner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  requester_staff_id: number;
  requester_name?: string;
  wfh_date: string;
  wfh_type: string;
  current_approval_status: ApprovalStatus;
  approving_officer: number;
  reason_description: string;
  supporting_doc_1?: string | null;
  supporting_doc_2?: string | null;
  supporting_doc_3?: string | null;
};

export const PendingRequests = () => {
  const [actionRequests, setActionRequests] = useState<TWFHRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<TWFHRequest[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user?.id;

  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(AlertStatus.Info);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});

  // Rejection modal state
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedArrangementId, setSelectedArrangementId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  // Document dialog state
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const fetchPendingRequests = async () => {
    if (!user || !userId) return;
    setLoading(true);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/arrangements/subordinates/${userId}`,
        { params: { current_approval_status: ["pending approval", "pending withdrawal"] } }
      );

      const requests = response.data.data
        .flatMap((dateEntry: any) => dateEntry.pending_arrangements)
        .filter((request: TWFHRequest) =>
          [ApprovalStatus.PendingApproval, ApprovalStatus.PendingWithdrawal].includes(request.current_approval_status)
        );
      console.log(requests);

      const requestsWithNames = await Promise.all(
        requests.map(async (request: TWFHRequest) => {
          const employee = await fetchEmployeeByStaffId(request.requester_staff_id);
          return {
            ...request,
            requester_name: employee ? `${employee.staff_fname} ${employee.staff_lname}` : "N/A",
          };
        })
      );

      setActionRequests(requestsWithNames);
      setFilteredRequests(requestsWithNames);
    } catch (error) {
      console.error("Failed to fetch subordinates' requests:", error);
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage("Failed to fetch requests.");
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data on component mount
  useEffect(() => {
    fetchPendingRequests();
  }, [user, userId]);

  // Refresh function to refetch data
  const refreshData = () => {
    fetchPendingRequests();
  };


  const handleRequestAction = async (
    action: Action,
    arrangement_id: number,
    reason_description: string,
    current_approval_status: ApprovalStatus
  ) => {
    const nextStatus =
      action === Action.Reject
        ? ApprovalStatus.Rejected
        : STATUS_ACTION_MAPPING[current_approval_status]?.[action];

    if (!nextStatus) {
      console.warn(`Action '${action}' is not allowed for status '${current_approval_status}'`);
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason_description", reason_description);
      formData.append("approving_officer", userId?.toString() || "");
      formData.append("current_approval_status", nextStatus);

      await axios.put(`${BACKEND_URL}/arrangements/${arrangement_id}/status`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setAlertStatus(AlertStatus.Success);
      setSnackbarMessage(`Request '${action}' successfully updated to status '${nextStatus}'`);
      setShowSnackbar(true);
      refreshData();
    } catch (error) {
      console.error(`Error performing action '${action}':`, error);
      setAlertStatus(AlertStatus.Error);
      setSnackbarMessage(`Error performing action '${action}'`);
      setShowSnackbar(true);
    } finally {
      setLoading(false);
      setRejectModalOpen(false);
    }
  };


  const handleRejectClick = (arrangementId: number) => {
    setSelectedArrangementId(arrangementId);
    setRejectModalOpen(true);
  };

  const handleConfirmReject = () => {
    if (selectedArrangementId && rejectionReason.trim()) {
      handleRequestAction(
        Action.Reject,
        selectedArrangementId,
        rejectionReason,
        ApprovalStatus.PendingApproval);
      setRejectionReason("");
    }
  };

  const handleCloseRejectModal = () => {
    setRejectModalOpen(false);
    setRejectionReason("");
  };

  const handleApplyFilters = (newFilters: any) => {
    setFilters(newFilters);
    const filtered = actionRequests.filter((request) => {
      const matchesDate =
        (!newFilters.startDate || new Date(request.wfh_date) >= newFilters.startDate) &&
        (!newFilters.endDate || new Date(request.wfh_date) <= newFilters.endDate);
      const matchesStatus =
        [ApprovalStatus.PendingApproval, ApprovalStatus.PendingWithdrawal].includes(request.current_approval_status);
      const searchQuery = newFilters.searchQuery?.toLowerCase() || "";
      const matchesSearchQuery =
        !searchQuery ||
        request.reason_description.toLowerCase().includes(searchQuery) ||
        request.wfh_type.toLowerCase().includes(searchQuery) ||
        request.wfh_date.includes(searchQuery) ||
        request.requester_staff_id.toString().includes(searchQuery) ||
        (request.requester_name && request.requester_name.toLowerCase().includes(searchQuery));
      return matchesDate && matchesStatus && matchesSearchQuery;
    });
    setFilteredRequests(filtered);
  };

  const handleViewDocuments = (docs: string[]) => {
    setDocuments(docs);
    setDocumentDialogOpen(true);
  };

  const handleCloseDocumentDialog = () => {
    setDocumentDialogOpen(false);
    setDocuments([]);
  };

  if (loading) {
    return (
      <Container sx={{ textAlign: "center", marginTop: 5 }}>
        <LoadingSpinner open={loading} />
      </Container>
    );
  }

  return (
    <>

      <Filters onApplyFilters={handleApplyFilters} onClearFilters={() => setFilteredRequests(actionRequests)} />

      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Action Required
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Staff Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Supporting Documents</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRequests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No pending requests
                </TableCell>
              </TableRow>
            ) : (
              filteredRequests.map((arrangement) => (
                <ArrangementRow
                  key={arrangement.arrangement_id}
                  arrangement={arrangement}
                  handleRequestAction={handleRequestAction}
                  handleRejectClick={handleRejectClick}
                  handleViewDocuments={handleViewDocuments}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={filteredRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) => setRowsPerPage(parseInt(event.target.value, 10))}
      />

      <SnackBarComponent
        showSnackbar={showSnackbar}
        handleCloseSnackBar={() => setShowSnackbar(false)}
        alertStatus={alertStatus}
        snackbarMessage={snackbarMessage}
      />

      {/* Rejection Reason Modal */}
      <Dialog open={rejectModalOpen} onClose={handleCloseRejectModal} fullWidth>
        <DialogTitle>Reject Request</DialogTitle>
        <DialogContent>
          <TextField
            data-cy="rejection-modal"
            label="Input a reason for rejection"
            fullWidth
            multiline
            rows={2}
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button data-cy='cancel-modal-button' onClick={handleCloseRejectModal} variant="outlined">
            Cancel
          </Button>
          <Button
            onClick={handleConfirmReject}
            color="error"
            disabled={!rejectionReason.trim()}
            variant="outlined"
            sx={{ m: 2 }}
            data-cy='reject-modal-button'
          >
            Reject Request
          </Button>
        </DialogActions>
      </Dialog>

      {/* Document Dialog */}
      <DocumentDialog
        isOpen={documentDialogOpen}
        documents={documents}
        onClose={handleCloseDocumentDialog}
      />
    </>
  );
};

// ArrangementRow Component
const ArrangementRow = ({
  arrangement,
  handleRequestAction,
  handleRejectClick,
  handleViewDocuments,
}: {
  arrangement: TWFHRequest;
  handleRequestAction: any;
  handleRejectClick: (arrangementId: number) => void;
  handleViewDocuments: (docs: string[]) => void;
}) => {
  const {
    arrangement_id,
    requester_staff_id,
    requester_name,
    wfh_date,
    wfh_type,
    current_approval_status,
    reason_description,
    supporting_doc_1,
    supporting_doc_2,
    supporting_doc_3,
  } = arrangement;

  const documents = [supporting_doc_1, supporting_doc_2, supporting_doc_3].filter(Boolean) as string[];

  return (
    <TableRow key={arrangement_id}>
      <TableCell>{requester_staff_id}</TableCell>
      <TableCell>{requester_name}</TableCell>
      <TableCell>{wfh_date}</TableCell>
      <TableCell>{wfh_type?.toUpperCase()}</TableCell>
      <TableCell>
        <Tooltip title="Scroll to view more">
          <Box sx={{ overflowX: "scroll", maxWidth: 200, whiteSpace: "nowrap" }}>
            {reason_description}
          </Box>
        </Tooltip>
      </TableCell>
      <TableCell>
        {documents.length > 0 ? (
          <Button variant="text" onClick={() => handleViewDocuments(documents)}>
            <Typography sx={{ textDecoration: "underline" }}>View more...</Typography>
          </Button>
        ) : (
          "NA"
        )}
      </TableCell>
      <TableCell>
        {current_approval_status === ApprovalStatus.PendingApproval ? (
          <>
            <ButtonGroup variant="contained">
              <Button
                color="success"
                startIcon={<CheckIcon />}
                data-cy={`approve-button-${arrangement.arrangement_id}`}
                onClick={() => handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)}
              >
                Approve
              </Button>
              <Button
                color="error"
                startIcon={<CloseIcon />}
                data-cy={`reject-button-${arrangement.arrangement_id}`}
                onClick={() => handleRejectClick(arrangement_id)}
              >
                Reject
              </Button>
            </ButtonGroup>
          </>
        ) : current_approval_status === ApprovalStatus.PendingWithdrawal ? (
          <>
            <ButtonGroup variant="contained">
              <Button
                color="warning" // orange color for "Withdraw"
                startIcon={<CheckIcon />}
                onClick={() => handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)}
              >
                Withdraw
              </Button>
              <Button
                color="error"
                startIcon={<CloseIcon />}
                onClick={() => handleRejectClick(arrangement_id)}
              >
                Reject
              </Button>
            </ButtonGroup>
          </>
        ) : null}
      </TableCell>
    </TableRow>
  );
};

// DocumentDialog Component
const DocumentDialog = ({
  isOpen,
  documents,
  onClose,
}: {
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
}) => (
  <Dialog open={isOpen} onClose={onClose} fullWidth>
    <DialogTitle>Supporting Documents</DialogTitle>
    <DialogContent>
      <List>
        {documents.map((document, idx) => (
          <ListItem key={document}>
            {idx + 1}.{" "}
            <Link href={document} target="_blank" rel="noopener noreferrer">
              Click to View...
            </Link>
          </ListItem>
        ))}
      </List>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>
        <CloseIcon />
      </Button>
    </DialogActions>
  </Dialog>
);
