import React from "react";
import { Button } from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";

interface ApproveButtonProps {
  arrangement_id: number;
  reason_description: string;
  onApprove: (id: number, reason: string) => void;
}

export const ApproveButton: React.FC<ApproveButtonProps> = ({
  arrangement_id,
  reason_description,
  onApprove,
}) => {
  const handleApprove = () => {
    onApprove(arrangement_id, reason_description);
  };

  return (
    <Button
      size="small"
      color="success"
      startIcon={<CheckIcon />}
      onClick={handleApprove}
    >
      Approve
    </Button>
  );
};

export default ApproveButton;
