import { useContext, useEffect, useState } from "react";
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
  CircularProgress,
} from "@mui/material";
import { ApprovalStatus } from "../../types/requests";
import { ChipProps } from "@mui/material/Chip";
import { UserContext } from "../../context/UserContextProvider";
import CloseIcon from "@mui/icons-material/Close";
import { capitalize } from "../../utils/utils";
import { DelegationStatus } from "../../types/delegation";
import { SnackBarComponent, AlertStatus } from "../../common/SnackBar";
import { TFilters, Filters } from "../../common/Filters";

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
  requester_info: {
    staff_fname: string;
    staff_lname: string;
  };
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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  const [filters, setFilters] = useState<TFilters>({
    startDate: null,
    endDate: null,
    workStatus: [],
    searchQuery: "",
  });

  const { user } = useContext(UserContext);
  const userId = user?.id;

  const [withdrawReason, setWithdrawReason] = useState("");
  const [selectedArrangementId, setSelectedArrangementId] = useState<
    number | null
  >(null);
  const [withdrawModalOpen, setWithdrawModalOpen] = useState(false);

  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState(AlertStatus.Info);
  const [withdrawLoading, setWithdrawLoading] = useState(false); // Initialize withdraw loading state

  const handleCloseSnackBar = () => setShowSnackbar(false);

  useEffect(() => {
    const fetchApprovedRequestsFromSubordinates = async () => {
      if (!user || !userId) return;

      try {
        const delegationResponse = await axios.get(
          `${BACKEND_URL}/employees/manager/viewdelegations/${userId}`
        );

        const delegationStatus = delegationResponse.data.status_of_delegation;
        const delegateManagerId = delegationResponse.data.delegate_manager_id;

        const managerIdToFetch =
          delegationStatus === DelegationStatus.Accepted && delegateManagerId
            ? delegateManagerId
            : userId;

        const response = await axios.get(
          `${BACKEND_URL}/arrangements/subordinates/${managerIdToFetch}`,
          {
            params: {
              current_approval_status: "approved",
              start_date: filters.startDate?.toISOString().split("T")[0],
              end_date: filters.endDate?.toISOString().split("T")[0],
              status: filters.workStatus.join(","),
              search_query: filters.searchQuery,
              items_per_page: rowsPerPage,
              page_num: page + 1,
            },
          }
        );

        const data: TWFHRequest[] = response.data.data;

        setApprovedRequests(data);
        setTotalItems(response.data.pagination_meta.total_count);
      } catch (error) {
        console.error("Failed to fetch approved requests:", error);
      }
    };

    fetchApprovedRequestsFromSubordinates();
  }, [user, userId, page, rowsPerPage, filters]);

  const handleFilterChange = (filters: TFilters) => {
    setFilters(filters);
  };

  const handleWithdrawApproval = async () => {
    if (!selectedArrangementId) return;
    setWithdrawLoading(true); // Set loading state to true
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
      setWithdrawReason("");
      setSnackbarMessage("Request withdrawn successfully.");
      setAlertStatus(AlertStatus.Success);
      setShowSnackbar(true); // Trigger snackbar
    } catch (error) {
      console.error("Error withdrawing approval:", error);
      setSnackbarMessage("Failed to withdraw request.");
      setAlertStatus(AlertStatus.Error);
      setShowSnackbar(true); // Trigger snackbar
    } finally {
      setWithdrawLoading(false); // Set loading state to false
    }
  };

  const openWithdrawModal = (arrangementId: number) => {
    setSelectedArrangementId(arrangementId);
    setWithdrawModalOpen(true);
  };

  return (
    <div data-cy="approved-requests-filter">
      <Typography variant="h4" gutterBottom align="left" sx={{ marginTop: 4 }}>
        Approved Requests
      </Typography>

      <Filters
        onApplyFilters={(newFilters) => handleFilterChange(newFilters)}
        onClearFilters={(newFilters) => handleFilterChange(newFilters)}
        excludeStatusFilter={true}
        excludeSearchFilter={true}
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
            {approvedRequests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No approved requests
                </TableCell>
              </TableRow>
            ) : (
              approvedRequests.map((arrangement) => (
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
        count={totalItems}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
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
            data-cy="withdrawal-reason-team"
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
            data-cy="withdraw-cancel-button-team"
          >
            Cancel
          </Button>
          <Button
            onClick={handleWithdrawApproval}
            color="warning"
            variant="outlined"
            disabled={!withdrawReason.trim() || withdrawLoading}
            data-cy="withdraw-button-team"
          >
            {withdrawLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Withdraw Request"
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar Component */}
      <SnackBarComponent
        showSnackbar={showSnackbar}
        handleCloseSnackBar={handleCloseSnackBar}
        alertStatus={alertStatus}
        snackbarMessage={snackbarMessage}
      />
    </div>
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
    wfh_date,
    wfh_type,
    current_approval_status,
    reason_description,
    supporting_doc_1,
    supporting_doc_2,
    supporting_doc_3,
    requester_info: { staff_fname: firstName, staff_lname: lastName },
  } = arrangement;

  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

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
        <TableCell>
          {firstName} {lastName}
        </TableCell>
        <TableCell>{wfh_date}</TableCell>
        <TableCell>{wfh_type?.toUpperCase()}</TableCell>
        <TableCell style={{ whiteSpace: "normal", wordWrap: "break-word" }}>
          {/* <Tooltip title="Scroll to view more">
            <Box
              sx={{ overflowX: "scroll", maxWidth: 200, whiteSpace: "nowrap" }}
            >
              {reason_description}
            </Box>
          </Tooltip> */}
          {reason_description}
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
            data-cy="withdraw-button-team"
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
