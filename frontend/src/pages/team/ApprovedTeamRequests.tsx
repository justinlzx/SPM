import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import {
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
  TextField,
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

type TArrangementByEmployee = {
  employee: TEmployee;
  approved_arrangements: TWFHRequest[];
};

export const ApprovedRequests = () => {
  const [approvedRequests, setApprovedRequests] = useState<TArrangementByEmployee[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  // State for modal handling
  const [withdrawReason, setWithdrawReason] = useState("");
  const [selectedArrangementId, setSelectedArrangementId] = useState<number | null>(null);
  const [withdrawModalOpen, setWithdrawModalOpen] = useState(false);

  // Fetch approved requests from subordinates
  useEffect(() => {
    const fetchApprovedRequestsFromSubordinates = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}/approved`
        );
        const approvedData: TArrangementByEmployee[] = response.data.data;
        setApprovedRequests(approvedData);
      } catch (error) {
        console.error("Failed to fetch approved requests:", error);
      }
    };
    fetchApprovedRequestsFromSubordinates();
  }, [user, userId]);

  const handleWithdrawApproval = async () => {
    if (!selectedArrangementId) return;
    try {
      const formData = new FormData();
      formData.append("action", "allow withdraw");
      formData.append("reason_description", withdrawReason);
      formData.append("approving_officer", userId?.toString() || "");
      formData.append("current_approval_status", ApprovalStatus.Withdrawn);
  
      await axios.put(
        `${BACKEND_URL}/arrangements/${selectedArrangementId}/status`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("Approval withdrawn successfully");
      setWithdrawModalOpen(false);
      setWithdrawReason(""); // Clear the reason field after submission
    } catch (error) {
      console.error("Error withdrawing approval:", error);
    }
  };

  const openWithdrawModal = (arrangementId: number) => {
    setSelectedArrangementId(arrangementId);
    setWithdrawModalOpen(true);
  };

  return (
    <>
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Approved Requests
      </Typography>
      <TableContainer component={Paper} sx={{ marginTop: 3, textAlign: "center" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Department</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Position</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Email</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Approved</TableCell>
            </TableRow>
          </TableHead>
          {approvedRequests.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} align="center">
                No approved requests
              </TableCell>
            </TableRow>
          ) : (
            approvedRequests.map((request) => {
              return (
                <EmployeeRow
                  request={request}
                  openWithdrawModal={openWithdrawModal}
                />
              );
            })
          )}
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={approvedRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) =>
          setRowsPerPage(parseInt(event.target.value, 10))
        }
      />

      {/* Withdraw Approval Modal */}
      <Dialog open={withdrawModalOpen} onClose={() => setWithdrawModalOpen(false)}>
        <DialogTitle>Withdraw Approval</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Withdrawal Reason"
            type="text"
            fullWidth
            value={withdrawReason}
            onChange={(e) => setWithdrawReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWithdrawModalOpen(false)} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleWithdrawApproval} color="primary">
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

const EmployeeRow = ({ request, openWithdrawModal }: TEmployeeRow) => {
  const {
    employee: { staff_id, staff_fname, staff_lname, dept, position, email },
  } = request;

  const arrangements = request.approved_arrangements.filter(
    (arrangement) => arrangement.current_approval_status === ApprovalStatus.Approved
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
      <TableRow key={request.employee.staff_id}>
        <TableCell>
          <Button onClick={() => setIsCollapsed(!isCollapsed)}>
            {isCollapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          </Button>
        </TableCell>
        <TableCell>{staff_id}</TableCell>
        <TableCell>
          {staff_fname} {staff_lname}
        </TableCell>
        <TableCell>{dept || "N/A"}</TableCell>
        <TableCell>{position}</TableCell>
        <TableCell>{email}</TableCell>
        <TableCell>
          <Chip variant="outlined" label={arrangements.length} /> 
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0, paddingLeft: 40, paddingRight: 0 }} colSpan={7}>
          <Collapse in={!isCollapsed} timeout="auto" unmountOnExit>
            <Box>
              <Table size="small">
                <TableHead>
                  <TableRow className="bg-gray-100">
                    <TableCell></TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Supporting Documents</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {arrangements.map((arrangement, idx) => {
                    const {
                      arrangement_id,
                      wfh_date,
                      wfh_type,
                      reason_description,
                      supporting_doc_1,
                      supporting_doc_2,
                      supporting_doc_3,
                    } = arrangement;

                    return (
                      <TableRow key={arrangement_id}>
                        <TableCell>{idx + 1}</TableCell>
                        <TableCell>{wfh_date}</TableCell>
                        <TableCell>{wfh_type?.toUpperCase()}</TableCell>
                        <TableCell sx={{ maxWidth: 200 }}>
                          <Tooltip title="Scroll to view more">
                            <Box sx={{ position: 'relative' }}>
                              <Box sx={{ overflowX: 'scroll', scrollbarWidth: 'none' }}>
                                {reason_description}
                              </Box>
                            </Box>
                          </Tooltip>
                        </TableCell>
                        <TableCell>
                          {supporting_doc_1 ||
                          supporting_doc_2 ||
                          supporting_doc_3 ? (
                            <Button
                              variant="text"
                              onClick={() =>
                                handleDialogOpen([
                                  supporting_doc_1,
                                  supporting_doc_2,
                                  supporting_doc_3,
                                ])
                              }
                              sx={{ textTransform: "none" }}
                            >
                              <Typography style={{ textDecoration: "underline" }}>View more ...</Typography>
                            </Button>
                          ) : (
                            "NA"
                          )}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            color="warning"
                            startIcon={<CheckIcon />}
                            onClick={() =>
                              openWithdrawModal(arrangement_id)
                            }
                          >
                            Withdraw Approval
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
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

type TEmployeeRow = {
  request: TArrangementByEmployee;
  openWithdrawModal: (arrangementId: number) => void;
};

type TDocumentDialog = {
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
};

const DocumentDialog = ({ isOpen, documents, onClose }: TDocumentDialog) => {
  return (
    <Dialog open={isOpen} onClose={onClose} fullWidth>
      <DialogTitle className="flex justify-between items-center" sx={{ paddingBottom: 0 }}>
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
              <Link href={document} target="_blank" rel="noopener noreferrer" className="ps-2">
                Click to View...
              </Link>
            </ListItem>
          ))}
        </List>
      </DialogContent>
    </Dialog>
  );
};
