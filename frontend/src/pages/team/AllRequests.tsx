import React, { useEffect, useState, useContext } from "react";
import axios from "axios";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Button,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  Link,
  Chip,
  Tooltip, 
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import { ApprovalStatus } from "../../types/status";
import { capitalize } from "../../utils/utils";
import { fetchEmployeeByStaffId } from "../../hooks/employee/employee.utils";

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

export const AllRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);
  const { user } = useContext(UserContext);
  const userId = user?.id;

  useEffect(() => {
    const fetchAllRequests = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}`
        );

        const allRequests: TWFHRequest[] = response.data.data.flatMap(
          (dateEntry: any) => dateEntry.pending_arrangements
        );

        const requestsWithNames = await Promise.all(
          allRequests.map(async (request: TWFHRequest) => {
            const employee = await fetchEmployeeByStaffId(request.requester_staff_id);
            return {
              ...request,
              requester_name: employee ? `${employee.staff_fname} ${employee.staff_lname}` : "N/A",
            };
          })
        );

        setRequests(requestsWithNames);
      } catch (error) {
        console.error("Failed to fetch all team requests:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAllRequests();
  }, [userId]);

  const handleDocumentDialogOpen = (docs: string[]) => {
    setDocuments(docs);
    setDocumentDialogOpen(true);
  };

  const handleDocumentDialogClose = () => {
    setDocumentDialogOpen(false);
    setDocuments([]);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <>
    
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Processed Team Requests
      </Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Staff Name</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Start Date</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Type</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Supporting Documents</TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>Status</TableCell>
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
                requests
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((request) => {
                    const docs = [
                      request.supporting_doc_1,
                      request.supporting_doc_2,
                      request.supporting_doc_3,
                    ].filter(Boolean) as string[];

                    return (
                      <TableRow key={request.arrangement_id}>
                        <TableCell>{request.requester_staff_id}</TableCell>
                        <TableCell>{request.requester_name}</TableCell>
                        <TableCell>{request.wfh_date}</TableCell>
                        <TableCell>{request.wfh_type?.toUpperCase() || "-"}</TableCell>
                        <TableCell>
                            <Tooltip title="Scroll to view more">
                            <Box sx={{ overflowX: "scroll", maxWidth: 150, whiteSpace: "nowrap" }}>
                                {request.reason_description}
                            </Box>
                            </Tooltip>
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
                            variant="outlined"
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          rowsPerPageOptions={[10, 20, 30]}
          count={requests.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />

      {/* Document Dialog */}
      <Dialog open={documentDialogOpen} onClose={handleDocumentDialogClose} fullWidth>
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
          <Button onClick={handleDocumentDialogClose}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AllRequests;
