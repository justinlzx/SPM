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
import { ApprovalStatus, Action, STATUS_ACTION_MAPPING } from "../../types/approvalStatus";
import { UserContext } from "../../context/UserContextProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  requester_staff_id: number;
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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user?.id;

  useEffect(() => {
    const fetchPendingRequestsFromSubordinates = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}`,
          {
            params: { current_approval_status: [ApprovalStatus.PendingApproval, ApprovalStatus.PendingWithdrawal] },
          }
        );
        const requests = response.data.data.flatMap((dateEntry: any) => dateEntry.pending_arrangements);
        setActionRequests(requests);
        console.log(requests);
      } catch (error) {
        console.error("Failed to fetch subordinates' requests:", error);
      }
    };
    fetchPendingRequestsFromSubordinates();
  }, [user, userId]);

  const handleRequestAction = async (
    action: Action,
    arrangement_id: number,
    reason_description: string,
    current_approval_status: ApprovalStatus
  ) => {
    const nextStatus = STATUS_ACTION_MAPPING[current_approval_status]?.[action];
    if (!nextStatus) {
      console.warn(`Action '${action}' is not allowed for status '${current_approval_status}'`);
      return;
    }

    try {
      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason_description", reason_description);
      formData.append("approving_officer", userId?.toString() || "");
      formData.append("current_approval_status", nextStatus);

      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      console.log(`Request '${action}' successfully updated to status '${nextStatus}'`);
    } catch (error) {
      console.error(`Error performing action '${action}':`, error);
    }
  };

  return (
    <>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Action Required
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Supporting Documents</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {actionRequests.filter(
              (request) =>
                request.current_approval_status === ApprovalStatus.PendingApproval ||
                request.current_approval_status === ApprovalStatus.PendingWithdrawal
            ).length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No pending requests
                </TableCell>
              </TableRow>
            ) : (
              actionRequests
                .filter(
                  (request) =>
                    request.current_approval_status === ApprovalStatus.PendingApproval ||
                    request.current_approval_status === ApprovalStatus.PendingWithdrawal
                )
                .map((arrangement) => (
                  <ArrangementRow
                    key={arrangement.arrangement_id}
                    arrangement={arrangement}
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
        onRowsPerPageChange={(event) => setRowsPerPage(parseInt(event.target.value, 10))}
      />
    </>
  );
};

// ArrangementRow Component
const ArrangementRow = ({ arrangement, handleRequestAction }: { arrangement: TWFHRequest; handleRequestAction: any }) => {
  const {
    arrangement_id,
    requester_staff_id,
    wfh_date,
    wfh_type,
    current_approval_status,
    reason_description,
    supporting_doc_1,
    supporting_doc_2,
    supporting_doc_3,
  } = arrangement;

  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const handleDialogOpen = () => {
    setDialogOpen(true);
    setDocuments([supporting_doc_1, supporting_doc_2, supporting_doc_3].filter(Boolean) as string[]);
  };

  return (
    <>
      <TableRow key={arrangement_id}>
        <TableCell>{requester_staff_id}</TableCell>
        <TableCell>{wfh_date}</TableCell>
        <TableCell>{wfh_type?.toUpperCase()}</TableCell>
        <TableCell sx={{ maxWidth: 200 }}>
          <Tooltip title="Scroll to view more">
            <Box sx={{ overflowX: 'scroll', scrollbarWidth: 'none' }}>
              {reason_description}
            </Box>
          </Tooltip>
        </TableCell>
        <TableCell>
          {documents.length ? (
            <Button variant="text" onClick={handleDialogOpen}>
              <Typography sx={{ textDecoration: "underline" }}>View more...</Typography>
            </Button>
          ) : "NA"}
        </TableCell>
        <TableCell>
          {current_approval_status === ApprovalStatus.PendingApproval && (
            <ButtonGroup variant="contained">
              <Button color="success" startIcon={<CheckIcon />} onClick={() =>
                handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)
              }>
                Approve
              </Button>
              <Button color="error" startIcon={<CloseIcon />} onClick={() =>
                handleRequestAction(Action.Reject, arrangement_id, reason_description, current_approval_status)
              }>
                Reject
              </Button>
            </ButtonGroup>
          )}
          {current_approval_status === ApprovalStatus.PendingWithdrawal && (
            <ButtonGroup variant="contained">
              <Button color="success" startIcon={<CheckIcon />} onClick={() =>
                handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)
              }>
                Approve Withdraw
              </Button>
              <Button color="error" startIcon={<CloseIcon />} onClick={() =>
                handleRequestAction(Action.Reject, arrangement_id, reason_description, current_approval_status)
              }>
                Reject
              </Button>
            </ButtonGroup>
          )}
        </TableCell>
      </TableRow>
      <DocumentDialog
        isOpen={dialogOpen}
        documents={documents}
        onClose={() => setDialogOpen(false)}
      />
    </>
  );
};

const DocumentDialog = ({ isOpen, documents, onClose }: { isOpen: boolean; documents: string[]; onClose: () => void; }) => (
  <Dialog open={isOpen} onClose={onClose} fullWidth>
    <DialogTitle sx={{ paddingBottom: 0 }}>Supporting Documents</DialogTitle>
    <DialogContent>
      <List>
        {documents.map((document, idx) => (
          <ListItem key={document}>
            {idx + 1}.
            <Link href={document} target="_blank" rel="noopener noreferrer">
              Click to View...
            </Link>
          </ListItem>
        ))}
      </List>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}><CloseIcon /></Button>
    </DialogActions>
  </Dialog>
);

