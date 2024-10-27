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
import { TEmployee } from "../../hooks/auth/employee/employee.utils";
import { ApprovalStatus } from "../../types/ApprovalStatus";
import { TWFHRequest } from "../../types/requests";
import { UserContext } from "../../context/UserContextProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type TAction = "approve" | "reject" | "allow withdraw";


type TArrangementByEmployee = {
  employee: TEmployee;
  pending_arrangements: TWFHRequest[];
};

export const PendingRequests = () => {
  const [actionRequests, setActionRequests] = useState<TArrangementByEmployee[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  // Fetch pending requests from subordinates
  useEffect(() => {
    const fetchPendingRequestsFromSubordinates = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}`,
        );
        console.log(response)
        const pendingRequests: TArrangementByEmployee[] = response.data.data;
        setActionRequests(pendingRequests);
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
    approval_status: ApprovalStatus
  ) => {
    try {
      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason_description", reason_description);
      formData.append("approving_officer", userId?.toString() || "");
      
      if (action === "allow withdraw") {
        formData.append("current_approval_status", ApprovalStatus.Withdrawn);
      }
      // else if (action === "pending withdrawal") {
      //   formData.append("current_approval_status", ApprovalStatus.Withdrawn);
      // }
      else if (action === "reject") {
        formData.append("current_approval_status", ApprovalStatus.Rejected);
      }
  
      await axios.put(
        `${BACKEND_URL}/arrangements/${arrangement_id}/status`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
  
      console.log(`Request ${action}d successfully`);
    } catch (error) {
      console.error(`Error ${action}ing request:`, error);
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
              {actionRequests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No pending requests
                  </TableCell>
                </TableRow>
              ) : (
                actionRequests.map((request) => {
                  return (
                    <EmployeeRow
                      request={request}
                      handleRequestAction={handleRequestAction}
                    />
                  );
                })
              )}
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

// EmployeeRow Component
const EmployeeRow = ({ request, handleRequestAction }: TEmployeeRow) => {
  const {
    employee: { staff_id, staff_fname, staff_lname, dept, position, email },
  } = request;

  const arrangements = request.pending_arrangements.filter(
    (arrangement) => 
      arrangement.approval_status === ApprovalStatus.PendingApproval ||
      arrangement.approval_status === ApprovalStatus.PendingWithdrawal
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
          <Chip label={arrangements.length} /> {/* Reintroducing the Chip component */}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell
          style={{
            paddingBottom: 0,
            paddingTop: 0,
            paddingLeft: 40,
            paddingRight: 0,
          }}
          colSpan={7}
        >
          <Collapse in={!isCollapsed} timeout="auto" unmountOnExit>
            <Box>
              <Table size="small">
                <TableHead>
                  <TableRow className="bg-gray-100">
                    <TableCell></TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
                    <TableCell sx={{ fontWeight: "bold" }}>
                      Supporting Documents
                    </TableCell>
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
                      approval_status,
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
                          {/* Conditionally render buttons based on status  */}
                          {approval_status === ApprovalStatus.PendingApproval && (
                            <ButtonGroup
                              variant="contained"
                              aria-label="Approve/Reject Button group"
                            >
                              <Button
                                size="small"
                                color="success"
                                startIcon={<CheckIcon />}
                                onClick={() =>
                                  handleRequestAction(
                                    "approve",
                                    arrangement_id,
                                    reason_description,
                                    approval_status
                                  )
                                }
                              >
                                Approve
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                startIcon={<CloseIcon />}
                                onClick={() =>
                                  handleRequestAction(
                                    "reject",
                                    arrangement_id,
                                    reason_description,
                                    approval_status
                                  )
                                }
                              >
                                Reject
                              </Button>
                            </ButtonGroup>
                          )}
                          {approval_status === ApprovalStatus.PendingWithdrawal && (
                            <ButtonGroup
                              variant="contained"
                              aria-label="Withdraw/Reject Button group"
                            >
                              <Button
                                size="small"
                                color="warning"
                                startIcon={<CheckIcon />}
                                onClick={() =>
                                  handleRequestAction(
                                    "allow withdraw",
                                    arrangement_id,
                                    reason_description,
                                    approval_status
                                  )
                                }
                              >
                                Allow Withdraw
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                startIcon={<CloseIcon />}
                                onClick={() =>
                                  handleRequestAction(
                                    "reject",
                                    arrangement_id,
                                    reason_description,
                                    approval_status
                                  )
                                }
                              >
                                Reject
                              </Button>
                            </ButtonGroup>
                          )}
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
