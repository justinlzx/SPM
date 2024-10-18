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
  Chip,
  Tooltip,
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { capitalize } from "../../utils/utils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Enum for approval statuses
export enum ApprovalStatus {
  Approved = "approved",
  PendingApproval = "pending approval",
  PendingWithdrawal = "pending withdrawal",
  Rejected = "rejected",
  Cancelled = "cancelled",
  Withdrawn = "withdrawn",
}

// Define types
type TAction = "approve" | "reject" | "allow withdraw";

export type TWFHRequest = {
  staff_id: number;
  requester_info: {
    staff_fname: string;
    staff_lname: string;
    dept: string;
    position: string;
  };
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  reason_description: string;
  approval_status: ApprovalStatus;
  supporting_doc_1: string;
  supporting_doc_2: string;
  supporting_doc_3: string;
};

type TArrangementsByDate = {
  date: string;
  pending_arrangements: TWFHRequest[];
};

export const PendingRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [actionRequests, setActionRequests] = useState<TArrangementsByDate[]>(
    []
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user!.id;

  // Get personal pending requests
  useEffect(() => {
    const fetchRequests = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/personal/${userId}`
        );
        // setActionRequests(response.data.data);
        const paginationMeta = response.data.pagination_meta;
        setRowsPerPage(paginationMeta.page_size);
      } catch (error) {
        console.error("Failed to fetch requests:", error);
      }
    };
    fetchRequests();
  }, [user, userId]);

  useEffect(() => {
    const fetchPendingRequestsFromSubordinates = async () => {
      if (!user || !userId) return;
      try {
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${userId}`,
          {
            params: {
              current_approval_status: ["pending approval", "pending withdrawal"],
            },
          }
        );
        const pendingRequests: TArrangementsByDate[] = response.data.data;
        const paginationMeta = response.data.pagination_meta;

        setActionRequests(pendingRequests);
        setRowsPerPage(paginationMeta.page_size);
      } catch (error) {
        console.error("Failed to fetch subordinates' requests:", error);
      }
    };
    fetchPendingRequestsFromSubordinates();
  }, [user, userId]);

  // Handle search input and filter the results
  const handleSearch = (searchTerm: string) => {
    const lowercasedTerm = searchTerm.toLowerCase();
    const updatedFilteredRequests = actionRequests.filter((request) =>
      request.employee.staff_id.toString().includes(lowercasedTerm) ||
      request.employee.staff_fname.toLowerCase().includes(lowercasedTerm) ||
      request.employee.staff_lname.toLowerCase().includes(lowercasedTerm) ||
      request.pending_arrangements.some((arrangement) =>
        arrangement.wfh_date.toLowerCase().includes(lowercasedTerm) ||
        arrangement.wfh_type.toLowerCase().includes(lowercasedTerm) ||
        arrangement.approval_status.toLowerCase().includes(lowercasedTerm)
      )
    );
    setFilteredRequests(updatedFilteredRequests);
  };

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
          <Search data={actionRequests} onSearchResult={setFilteredRequests} />
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
                  <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    No. of Requests
                  </TableCell>
                </TableRow>
              </TableHead>
              {filteredRequests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No pending requests
                  </TableCell>
                </TableRow>
              ) : (
                filteredRequests.map((request) => {
                  return (
                    <DateRow
                      date={request}
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
            count={filteredRequests.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(event) =>
              setRowsPerPage(parseInt(event.target.value, 10))
            }
          />
        </>
  );
};

type TDateRow = {
  date: TArrangementsByDate;
  handleRequestAction: (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => {};
};

const DateRow = ({ date, handleRequestAction }: TDateRow) => {
  const arrangements = date.pending_arrangements;

  const [isCollapsed, setIsCollapsed] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const handleDialogOpen = (documents: string[]) => {
    setDialogOpen(true);
    setDocuments(documents);
  };

  return (
    <>
      <TableRow>
        <TableCell>
          <Button onClick={() => setIsCollapsed(!isCollapsed)}>
            {isCollapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          </Button>
        </TableCell>
        <TableCell>{date.date}</TableCell>
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
          colSpan={3}
        >
          <Collapse in={!isCollapsed} timeout="auto" unmountOnExit>
            <Box>
              <Table size="small">
                <TableHead>
                  <TableRow className="bg-gray-100">
                    <TableCell></TableCell>
                    <TableCell>Staff ID</TableCell>
                    <TableCell>Staff Name</TableCell>
                    <TableCell>Department</TableCell>
                    <TableCell>Position</TableCell>
                    <TableCell>Email</TableCell>
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
                      staff_id,
                      requester_info: {
                        staff_fname,
                        staff_lname,
                        dept,
                        position,
                      },
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
                        <TableCell>{staff_id}</TableCell>
                        <TableCell>
                          {staff_fname} {staff_lname}
                        </TableCell>
                        <TableCell>{dept}</TableCell>
                        <TableCell>{position}</TableCell>
                        <TableCell>{wfh_type?.toUpperCase()}</TableCell>
                        <TableCell className="max-w-[200px]">
                          <Tooltip title="Scroll to view more">
                            <div className="relative">
                              <div className="overflow-x-scroll scrollbar-hide">
                                {reason_description}
                              </div>
                            </div>
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
                              <u>View more ...</u>
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
