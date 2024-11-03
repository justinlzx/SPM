import React from "react";
import { TableCell, TableRow, ButtonGroup, Button } from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { TWFHRequest, ApprovalStatus, TAction } from "../../types/requests";

type EmployeeRowProps = {
  request: TWFHRequest;
  openDocumentDialog: (documents: string[]) => void;
  handleRequestAction?: (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => void;
};

const EmployeeRow: React.FC<EmployeeRowProps> = ({
  request,
  openDocumentDialog,
  handleRequestAction
}) => {
  const {
    arrangement_id,
    requester_staff_id,
    requester_info,
    wfh_type,
    reason_description,
    supporting_doc_1,
    supporting_doc_2,
    supporting_doc_3,
    current_approval_status
  } = request;

  // Filter documents to only include non-null values
  const documents = [supporting_doc_1, supporting_doc_2, supporting_doc_3].filter(Boolean) as string[];

  return (
    <TableRow>
      <TableCell>{requester_staff_id}</TableCell>
      <TableCell>
        {requester_info ? `${requester_info.staff_fname} ${requester_info.staff_lname}` : "N/A"}
      </TableCell>
      <TableCell>{requester_info?.dept || "N/A"}</TableCell>
      <TableCell>{requester_info?.position || "N/A"}</TableCell>
      <TableCell>{wfh_type || "N/A"}</TableCell>
      <TableCell>{reason_description || "N/A"}</TableCell>
      <TableCell>
        {documents.length > 0 ? (
          <Button variant="text" onClick={() => openDocumentDialog(documents)}>
            View Documents
          </Button>
        ) : (
          "None"
        )}
      </TableCell>
      <TableCell>
        {current_approval_status === ApprovalStatus.PendingApproval && handleRequestAction && (
          <ButtonGroup>
            <Button onClick={() => handleRequestAction("approve", arrangement_id, reason_description)}>
              <CheckIcon /> Approve
            </Button>
            <Button onClick={() => handleRequestAction("reject", arrangement_id, reason_description)}>
              <CloseIcon /> Reject
            </Button>
          </ButtonGroup>
        )}
      </TableCell>
    </TableRow>
  );
};

export default EmployeeRow;
