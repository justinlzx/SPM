import React, { useContext, useEffect, useState } from "react";
import axios from "axios";
import {
  Chip,
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
  TextField,
  Tooltip,
  Box,
  Link,
  List,
  ListItem,
} from "@mui/material";
import { ApprovalStatus } from "../../types/requests";
import { ChipProps } from "@mui/material/Chip";
import { UserContext } from "../../context/UserContextProvider";
import CloseIcon from "@mui/icons-material/Close";
import { fetchEmployeeByStaffId } from "../../hooks/employee/employee.utils";
import { capitalize } from "../../utils/utils";
import { DelegationStatus } from "../../types/delegation";
import Filters from "../../common/Filters"; // Import the Filters component

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

const getChipColor = (
  status: ApprovalStatus | undefined
): ChipProps["color"] => {
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

export const ApprovedRequests = () => {
  const [approvedRequests, setApprovedRequests] = useState<TWFHRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<TWFHRequest[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { user } = useContext(UserContext);
  const userId = user?.id;

  const [withdrawReason, setWithdrawReason] = useState("");
  const [selectedArrangementId, setSelectedArrangementId] = useState<
    number | null
  >(null);
  const [withdrawModalOpen, setWithdrawModalOpen] = useState(false);

  useEffect(() => {
    const fetchApprovedRequestsFromSubordinates = async () => {
      if (!user || !userId) return;

      try {
        // Step 1: Fetch the delegation status to determine the manager to fetch data for
        const delegationResponse = await axios.get(
          `${BACKEND_URL}/employees/manager/viewdelegations/${userId}`
        );
        const delegationStatus = delegationResponse.data.status_of_delegation;
        const delegateManagerId = delegationResponse.data.delegate_manager_id;

        // Step 2: Determine the manager ID to fetch requests for
        const managerIdToFetch =
          delegationStatus === DelegationStatus.Accepted && delegateManagerId
            ? delegateManagerId
            : userId;

        // Step 3: Fetch approved requests for the determined manager ID
        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${managerIdToFetch}`,
          {
            params: {
              current_approval_status: "approved",
            },
          }
        );

        // Step 4: Process and filter the fetched requests
        const approvedData: TWFHRequest[] = response.data.data;

        // Step 5: Attach requester names to each request
        const requestsWithNames = await Promise.all(
          approvedData.map(async (request) => {
            const employee = await fetchEmployeeByStaffId(
              request.requester_staff_id
            );
            return {
              ...request,
              requester_name: employee
                ? `${employee.staff_fname} ${employee.staff_lname}`
                : "N/A",
            };
          })
        );

        setApprovedRequests(requestsWithNames);
        setFilteredRequests(requestsWithNames); // Initialize filtered requests
      } catch (error) {
        console.error("Failed to fetch approved requests:", error);
      }
    };

    fetchApprovedRequestsFromSubordinates();
  }, [user, userId]);

  // Handle filter application
  const onApplyFilters = (filters: {
    startDate: Date | null;
    endDate: Date | null;
    department: string[];
    status: ApprovalStatus[];
    searchQuery: string;
    workStatus: string[];
  }) => {
    const filtered = approvedRequests.filter((request) => {
      const matchesDate =
        (!filters.startDate ||
          new Date(request.wfh_date) >= filters.startDate) &&
        (!filters.endDate || new Date(request.wfh_date) <= filters.endDate);

      const matchesStatus =
        filters.status.length === 0 ||
        filters.status.includes(request.current_approval_status);

      const searchQuery = filters.searchQuery.toLowerCase();
      const matchesSearchQuery =
        !searchQuery ||
        request.reason_description.toLowerCase().includes(searchQuery) ||
        request.wfh_type.toLowerCase().includes(searchQuery) ||
        request.wfh_date.includes(searchQuery) ||
        request.requester_staff_id.toString().includes(searchQuery) ||
        (request.requester_name &&
          request.requester_name.toLowerCase().includes(searchQuery));

      return matchesDate && matchesStatus && matchesSearchQuery;
    });
    setFilteredRequests(filtered);
  };

  // Handle filter clearing
  const onClearFilters = () => {
    setFilteredRequests(approvedRequests);
  };

  const handleWithdrawApproval = async () => {
    if (!selectedArrangementId) return;
    try {
      const formData = new FormData();
      formData.append("action", "withdraw");
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

      {/* Filters Component */}
      <Filters
        onApplyFilters={onApplyFilters}
        onClearFilters={onClearFilters}
      />

      <TableContainer
        component={Paper}
        sx={{ marginTop: 3, textAlign: "center" }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: "bold" }}>Staff ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Staff Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Date</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>WFH Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Reason</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>
                Supporting Documents
              </TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Status</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRequests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No approved requests
                </TableCell>
              </TableRow>
            ) : (
              filteredRequests.map((arrangement) => (
                <ArrangementRow
                  key={arrangement.arrangement_id}
                  arrangement={arrangement}
                  openWithdrawModal={openWithdrawModal}
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
        onRowsPerPageChange={(event) =>
          setRowsPerPage(parseInt(event.target.value, 10))
        }
      />

      {/* Withdraw Approval Modal */}
      <Dialog
        open={withdrawModalOpen}
        onClose={() => setWithdrawModalOpen(false)}
        sx={{ "& .MuiDialog-paper": { minWidth: "400px" } }}
      >
        <DialogTitle>Withdraw Employee WFH Request</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="Input a reason for withdrawal"
            fullWidth
            multiline
            rows={2}
            sx={{ mt: 2 }}
            margin="dense"
            type="text"
            value={withdrawReason}
            onChange={(e) => setWithdrawReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setWithdrawModalOpen(false)}
            color="secondary"
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleWithdrawApproval}
            color="warning"
            variant="outlined"
            disabled={!withdrawReason.trim()}
          >
            Withdraw Request
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// ArrangementRow Component
const ArrangementRow = ({
  arrangement,
  openWithdrawModal,
}: {
  arrangement: TWFHRequest;
  openWithdrawModal: (arrangementId: number) => void;
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

  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const formattedDate = new Date(wfh_date).toLocaleDateString("en-GB");

  const handleDialogOpen = () => {
    setDialogOpen(true);
    setDocuments(
      [supporting_doc_1, supporting_doc_2, supporting_doc_3].filter(
        Boolean
      ) as string[]
    );
  };

  return (
    <>
      <TableRow key={arrangement_id}>
        <TableCell>{requester_staff_id}</TableCell>
        <TableCell>{requester_name}</TableCell>
        <TableCell>{wfh_date}</TableCell>
        <TableCell>{wfh_type?.toUpperCase()}</TableCell>
        <TableCell sx={{ maxWidth: 200 }}>
          <Tooltip title="Scroll to view more">
            <Box
              sx={{ overflowX: "scroll", maxWidth: 200, whiteSpace: "nowrap" }}
            >
              {reason_description}
            </Box>
          </Tooltip>
        </TableCell>
        <TableCell>
          {documents.length > 0 ? (
            <Button variant="text" onClick={handleDialogOpen}>
              View Documents
            </Button>
          ) : (
            "None"
          )}
        </TableCell>
        <TableCell>
          <Chip
            color={getChipColor(current_approval_status)}
            label={capitalize(current_approval_status)}
          />
        </TableCell>
        <TableCell>
          <Button
            color="warning"
            variant="outlined"
            onClick={() => openWithdrawModal(arrangement_id)}
          >
            Withdraw
          </Button>
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
              View Document
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

export default ApprovedRequests;
