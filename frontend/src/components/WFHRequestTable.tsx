import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Modal,
  Box,
  Typography,
  CircularProgress,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  Link,
} from "@mui/material";
import axios from "axios";
import { ChipProps } from "@mui/material/Chip";
import { ApprovalStatus } from "../types/status";
import { capitalize } from "../utils/utils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

type TWFHRequest = {
  arrangement_id: number;
  requester_staff_id: number;
  wfh_date: string;
  end_date?: string;
  wfh_type: string;
  reason_description: string;
  current_approval_status: ApprovalStatus;
  supporting_doc_1?: string | null;
  supporting_doc_2?: string | null;
  supporting_doc_3?: string | null;
};

type TWFHRequestTableProps = {
  requests: TWFHRequest[];
  handleSuccess: (id: number, action: "cancel" | "withdraw") => void;
};

const getChipColor = (status: ApprovalStatus | undefined): ChipProps["color"] => {
  if (!status) return "default";
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.PendingApproval:
    case ApprovalStatus.PendingWithdrawal:
      return "warning";
    case ApprovalStatus.Rejected:
      return "error";
    default:
      return "default";
  }
};

// Confirmation modal component for cancel/withdraw actions
const ConfirmationModal: React.FC<{
  open: boolean;
  action: "cancel" | "withdraw" | undefined;
  handleClose: () => void;
  handleConfirm: () => void;
  loading: boolean;
  reason: string;
  setReason: React.Dispatch<React.SetStateAction<string>>;
}> = ({
  open,
  action,
  handleClose,
  handleConfirm,
  loading,
  reason,
  setReason,
}) => (
  <Modal open={open} onClose={handleClose}>
    <Box
      sx={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: 400,
        bgcolor: "background.paper",
        borderRadius: 2,
        p: 4,
        boxShadow: 24,
      }}
    >
      <Typography variant="h6">
        Confirm {action === "cancel" ? "Cancellation" : "Withdrawal"}
      </Typography>
      <Typography mb={2}>
        Are you sure you want to {action === "cancel" ? "cancel" : "withdraw"}{" "}
        this request?
      </Typography>
      {action === "withdraw" && (
        <TextField
          label="Reason for withdrawal (Optional)"
          fullWidth
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          margin="normal"
        />
      )}
      <Box mt={2} display="flex" justifyContent="flex-end">
        <Button onClick={handleClose} variant="outlined" color="secondary" sx={{ mr: 2 }}>
          No
        </Button>
        <Button onClick={handleConfirm} variant="contained" color="primary" disabled={loading}>
          {loading ? <CircularProgress size={24} color="inherit" /> : "Yes"}
        </Button>
      </Box>
    </Box>
  </Modal>
);

// DocumentDialog component for viewing supporting documents
const DocumentDialog: React.FC<{
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
}> = ({ isOpen, documents, onClose }) => (
  <Dialog open={isOpen} onClose={onClose} fullWidth>
    <DialogTitle>Supporting Documents</DialogTitle>
    <DialogContent>
      <List>
        {documents.map((document, idx) => (
          <ListItem key={document}>
            {idx + 1}.{" "}
            <Link href={document} target="_blank" rel="noopener noreferrer">
              View Document
            </Link>
          </ListItem>
        ))}
      </List>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>
        Close
      </Button>
    </DialogActions>
  </Dialog>
);

export const WFHRequestTable: React.FC<TWFHRequestTableProps> = ({
  requests,
  handleSuccess,
}) => {
  const [open, setOpen] = useState(false);
  const [action, setAction] = useState<"cancel" | "withdraw">();
  const [selectedArrangementId, setSelectedArrangementId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState<string>("");

  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const handleOpen = (arrangementId: number, action: "cancel" | "withdraw") => {
    setSelectedArrangementId(arrangementId);
    setAction(action);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedArrangementId(null);
    setAction(undefined);
    setReason("");
  };

  const handleDocumentDialogOpen = (docs: string[]) => {
    setDocuments(docs);
    setDocumentDialogOpen(true);
  };

  const handleDocumentDialogClose = () => {
    setDocumentDialogOpen(false);
    setDocuments([]);
  };

  const handleWithdrawal = async () => {
    // Same withdrawal logic as previously implemented
  };

  const handleCancellation = async () => {
    // Same cancellation logic as previously implemented
  };

  return (
    <>
      <TableContainer component={Paper} sx={{ marginTop: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Staff ID</TableCell>
              <TableCell>Start Date</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Supporting Documents</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No requests found
                </TableCell>
              </TableRow>
            ) : (
              requests.map((request) => {
                const docs = [
                  request.supporting_doc_1,
                  request.supporting_doc_2,
                  request.supporting_doc_3,
                ].filter(Boolean) as string[];

                return (
                  <TableRow key={request.arrangement_id}>
                    <TableCell>{request.requester_staff_id}</TableCell>
                    <TableCell>{request.wfh_date}</TableCell>
                    <TableCell>{request.wfh_type?.toUpperCase() || "-"}</TableCell>
                    <TableCell
                      sx={{
                        maxWidth: "200px",
                        wordBreak: "break-word",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        padding: 1,
                      }}
                    >
                      {request.reason_description || "-"}
                    </TableCell>
                    <TableCell>
                      {docs.length > 0 ? (
                        <Button variant="text" onClick={() => handleDocumentDialogOpen(docs)}>
                          View Documents
                        </Button>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        color={getChipColor(request.current_approval_status)}
                        label={capitalize(request.current_approval_status)}
                        variant={
                          request.current_approval_status ===
                          ApprovalStatus.PendingWithdrawal
                            ? "outlined"
                            : "filled"
                        }
                      />
                    </TableCell>
                    <TableCell>
                      {request.current_approval_status === ApprovalStatus.PendingApproval && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="primary"
                          onClick={() => handleOpen(request.arrangement_id, "cancel")}
                        >
                          Cancel
                        </Button>
                      )}
                      {request.current_approval_status === ApprovalStatus.Approved && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="secondary"
                          onClick={() => handleOpen(request.arrangement_id, "withdraw")}
                        >
                          Withdraw
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <ConfirmationModal
        open={open}
        action={action}
        handleClose={handleClose}
        handleConfirm={action === "cancel" ? handleCancellation : handleWithdrawal}
        loading={loading}
        reason={reason}
        setReason={setReason}
      />

      <DocumentDialog
        isOpen={documentDialogOpen}
        documents={documents}
        onClose={handleDocumentDialogClose}
      />
    </>
  );
};
