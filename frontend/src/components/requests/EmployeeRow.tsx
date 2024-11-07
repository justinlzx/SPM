import React, { useState } from "react";
import {
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableRow,
  IconButton,
  Box,
  Typography,
  Button,
  ButtonGroup,
  Tooltip,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { ApprovalStatus, Action } from "../../types/status";
import { TWFHRequest } from "../../pages/team/PendingRequests";

type TEmployeeRow = {
  employeeName: string;
  staffId: number;
  requests: TWFHRequest[];
  handleRequestAction: (
    action: Action,
    arrangement_id: number,
    reason_description: string,
    approval_status: ApprovalStatus
  ) => Promise<void>;
  handleRejectClick: (arrangementId: number) => void;
  handleViewDocuments: (docs: string[]) => void;
};

export const EmployeeRow = ({
  employeeName,
  staffId,
  requests,
  handleRequestAction,
  handleRejectClick,
  handleViewDocuments,
}: TEmployeeRow) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{staffId}</TableCell>
        <TableCell>{employeeName}</TableCell>
        <TableCell>{requests.length}</TableCell>
      </TableRow>

      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box margin={1}>
              <Typography variant="h6" gutterBottom component="div">
                Requests
              </Typography>
              <Table size="small">
                <TableBody>
                  {requests.map((request) => (
                    <ArrangementRow
                      key={request.arrangement_id}
                      arrangement={request}
                      handleRequestAction={handleRequestAction}
                      handleRejectClick={handleRejectClick}
                      handleViewDocuments={handleViewDocuments}
                    />
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

// ArrangementRow Component (you can use the previous definition you had for it)
const ArrangementRow = ({
  arrangement,
  handleRequestAction,
  handleRejectClick,
  handleViewDocuments,
}: {
  arrangement: TWFHRequest;
  handleRequestAction: any;
  handleRejectClick: (arrangementId: number) => void;
  handleViewDocuments: (docs: string[]) => void;
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

  const documents = [supporting_doc_1, supporting_doc_2, supporting_doc_3].filter(Boolean) as string[];

  return (
    <TableRow key={arrangement_id}>
      <TableCell>{requester_staff_id}</TableCell>
      <TableCell>{requester_name}</TableCell>
      <TableCell>{wfh_date}</TableCell>
      <TableCell>{wfh_type?.toUpperCase()}</TableCell>
      <TableCell>
        <Tooltip title="Scroll to view more">
          <Box sx={{ overflowX: "scroll", maxWidth: 200, whiteSpace: "nowrap" }}>
            {reason_description}
          </Box>
        </Tooltip>
      </TableCell>
      <TableCell>
        {documents.length > 0 ? (
          <Button variant="text" onClick={() => handleViewDocuments(documents)}>
            <Typography sx={{ textDecoration: "underline" }}>View more...</Typography>
          </Button>
        ) : (
          "NA"
        )}
      </TableCell>
      <TableCell>
        {current_approval_status === ApprovalStatus.PendingApproval ? (
          <>
            <ButtonGroup variant="contained">
              <Button
                color="success"
                startIcon={<CheckIcon />}
                onClick={() => handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)}
              >
                Approve
              </Button>
              <Button
                color="error"
                startIcon={<CloseIcon />}
                onClick={() => handleRejectClick(arrangement_id)}
              >
                Reject
              </Button>
            </ButtonGroup>
          </>
        ) : current_approval_status === ApprovalStatus.PendingWithdrawal ? (
          <>
            <ButtonGroup variant="contained">
              <Button
                color="warning"
                startIcon={<CheckIcon />}
                onClick={() => handleRequestAction(Action.Approve, arrangement_id, reason_description, current_approval_status)}
              >
                Allow Withdraw
              </Button>
              <Button
                color="error"
                startIcon={<CloseIcon />}
                onClick={() => handleRejectClick(arrangement_id)}
              >
                Reject
              </Button>
            </ButtonGroup>
          </>
        ) : null}
      </TableCell>
    </TableRow>
  );
};
