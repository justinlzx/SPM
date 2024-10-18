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
  TextField,
  Chip,
  ChipProps,
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
} from "@mui/material";
import { UserContext } from "../../context/UserContextProvider";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { TEmployee } from "../../hooks/auth/employee/employee.utils";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { capitalize } from "../../utils/utils";


const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Define types
type TAction = "approve" | "reject";

enum ApprovalStatus {
  Approved = "approved",
  Pending = "pending",
  Rejected = "rejected",
}

type TWFHRequest = {
  staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  reason_description: string; // Include reason_description here
  approval_status: ApprovalStatus;
  supporting_doc_1: string;
  supporting_doc_2: string;
  supporting_doc_3: string;
};

type TArrangementByEmployee = {
  employee: TEmployee;
  pending_arrangements: TWFHRequest[];
};

const getChipColor = (status: ApprovalStatus): ChipProps["color"] => {
  switch (status) {
    case ApprovalStatus.Approved:
      return "success";
    case ApprovalStatus.Pending:
      return "warning";
    case ApprovalStatus.Rejected:
      return "error";
    default:
      return "default"; // Fallback if needed
  }
};

export const PendingRequests = () => {
  const [requests, setRequests] = useState<TWFHRequest[]>([]);
  const [actionRequests, setActionRequests] = useState<
    TArrangementByEmployee[]
  >([]);
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
        const allRequests: TWFHRequest[] = response.data.data;

        // Filter for pending requests, excluding Jack Sim's approved requests
        const filteredRequests = allRequests.filter((request: TWFHRequest) => {
          if (
            request.staff_id === 130002 &&
            request.approval_status === ApprovalStatus.Approved
          ) {
            return false;
          }
          return request.approval_status === ApprovalStatus.Pending;
        });

        setRequests(filteredRequests);
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
              current_approval_status: "pending",
            },
          }
        );
        const pendingRequests: TArrangementByEmployee[] = response.data.data;
        setActionRequests(pendingRequests);
      } catch (error) {
        console.error("Failed to fetch subordinates' requests:", error);
      }
    };
    fetchPendingRequestsFromSubordinates();
  }, [user, userId]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleRequestAction = async (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => {
    try {
      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason_description", reason_description);
      formData.append("approving_officer", userId?.toString() || "");

      // Log the payload before sending it
      console.log("Payload being sent:", {
        reason_description,
        action,
        approving_officer: userId,
        arrangement_id,
      });

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

  // TODO: remove this when filtering with backend is implemented
  const filteredRequests = requests.filter(
    (request) =>
      request.staff_id.toString().includes(searchTerm) ||
      request.wfh_date.includes(searchTerm) ||
      request.wfh_type.toLowerCase().includes(searchTerm) ||
      request.approval_status.toLowerCase().includes(searchTerm)
  );

  return (
    <Container>
      <TextField
        label="Search"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={handleSearch}
      />

      {/* Table for an employees Pending Requests */}
      {/* <Typography
        gutterBottom
        align="left"
        sx={{ marginTop: 4 }}
      >
        My Pending Requests
      </Typography>
      <TableContainer
        component={Paper}
        sx={{ marginTop: 3, textAlign: "center" }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>{" "}
              <TableCell sx={{ fontWeight: "bold" }}>Approval Status</TableCell>
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
              requests.map((request) => {
                const {
                  arrangement_id,
                  wfh_date,
                  wfh_type,
                  reason_description,
                  staff_id,
                } = request;
                return (
                  <TableRow key={arrangement_id}>
                    <TableCell>{staff_id}</TableCell>
                    <TableCell>{wfh_date}</TableCell>
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
                      <Chip
                        label={capitalize(request.approval_status)}
                        color={getChipColor(request.approval_status)}
                      />
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer> */}
      {/* <TablePagination
        component="div"
        rowsPerPageOptions={[10, 20, 30]}
        count={filteredRequests.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) =>
          setRowsPerPage(parseInt(event.target.value, 10))
        }
      /> */}
      {user!.role !== 3 && (
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

          {/* TODO: amend this for backend filtering */}
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
      )}
    </Container>
  );
};

type TEmployeeRow = {
  request: TArrangementByEmployee;
  handleRequestAction: (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => {};
};

const EmployeeRow = ({ request, handleRequestAction }: TEmployeeRow) => {
  const {
    employee: { staff_id, staff_fname, staff_lname, dept, position, email },
  } = request;

  const arrangements = request.pending_arrangements;

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
          <Chip label={arrangements.length}></Chip>
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
                    } = arrangement;
                    return (
                      <TableRow key={arrangement_id}>
                        <TableCell>{idx + 1}</TableCell>
                        <TableCell>{wfh_date}</TableCell>
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
                                  reason_description
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
                                  reason_description
                                )
                              }
                            >
                              Reject
                            </Button>
                          </ButtonGroup>
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
