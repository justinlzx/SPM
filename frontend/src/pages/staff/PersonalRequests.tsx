import React, { useEffect, useState, useContext } from "react";
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  Link,
} from "@mui/material";
import axios from "axios";
import { UserContext } from "../../context/UserContextProvider";
import { ApprovalStatus } from "../../types/status";
import { capitalize } from "../../utils/utils";
import { TWFHRequest } from "../../types/requests";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const getChipColor = (status: ApprovalStatus) => {
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.Rejected:
      return "error";
    case ApprovalStatus.PendingApproval:
    case ApprovalStatus.PendingWithdrawal:
      return "warning";
    default:
      return "default";
  }
};

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
      <Button onClick={onClose}>Close</Button>
    </DialogActions>
  </Dialog>
);

export const PersonalRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [, setApprovedCount] = useState<number>(0);
  const [, setApprovedThisMonth] = useState<number>(0);
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);
  const { user } = useContext(UserContext);
  const userId = user?.id;

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );

        const allRequests: TWFHRequest[] = response.data.data;
        setRequests(allRequests);

        // Calculate approved requests count
        const approvedRequestsCount = allRequests.filter(
          (request) => request.current_approval_status === ApprovalStatus.Approved
        ).length;
        setApprovedCount(approvedRequestsCount);

        // Calculate approved WFH days for the current month
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
        const approvedThisMonthCount = allRequests.filter((request) => {
          const requestDate = new Date(request.wfh_date);
          return (
            request.current_approval_status === ApprovalStatus.Approved &&
            requestDate.getMonth() === currentMonth &&
            requestDate.getFullYear() === currentYear
          );
        }).length;

        setApprovedThisMonth(approvedThisMonthCount);

      } catch (error) {
        console.error("Failed to fetch WFH requests:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRequests();
  }, [userId]);

  const handleDocumentDialogOpen = (docs: string[]) => {
    setDocuments(docs);
    setDocumentDialogOpen(true);
  };

  const handleDocumentDialogClose = () => {
    setDocumentDialogOpen(false);
    setDocuments([]);
  };

  return (
    <>
      <TableContainer component={Paper} sx={{ marginTop: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Staff ID</TableCell>
              <TableCell>Start Date</TableCell>
              <TableCell>End Date</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Supporting Documents</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : requests.length === 0 ? (
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
                    <TableCell>{request.end_date || "-"}</TableCell>
                    <TableCell>{request.wfh_type?.toUpperCase() || "-"}</TableCell>
                    <TableCell
                      sx={{
                        maxWidth: "200px",
                        wordBreak: "break-word",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
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
                        "None"
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        color={getChipColor(request.current_approval_status)}
                        label={capitalize(
                          request.current_approval_status
                            ? request.current_approval_status
                            : "Unknown Status"
                        )}
                        variant={
                          request.current_approval_status ===
                          ApprovalStatus.PendingWithdrawal
                            ? "outlined"
                            : "filled"
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

      {/* Document Dialog */}
      <DocumentDialog
        isOpen={documentDialogOpen}
        documents={documents}
        onClose={handleDocumentDialogClose}
      />
    </>
  );
};

export default PersonalRequests;
