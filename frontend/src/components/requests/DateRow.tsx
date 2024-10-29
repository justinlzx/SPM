import React, { useState } from "react";
import {
  TableRow,
  TableCell,
  Chip,
  Button,
  Collapse,
  Box,
} from "@mui/material";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { TArrangementsByDate, TAction } from "../../types/requests";
import EmployeeRow from "../../components/requests/EmployeeRow";
import DocumentDialog from "../../components/requests/DocumentDialog";

type DateRowProps = {
  date: TArrangementsByDate;
  handleRequestAction?: (
    action: TAction,
    arrangement_id: number,
    reason_description: string
  ) => void;
};

export const DateRow: React.FC<DateRowProps> = ({ date, handleRequestAction }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  // This function opens the dialog with the specified documents
  const openDocumentDialog = (docs: string[]) => {
    setDialogOpen(true);
    setDocuments(docs);
  };

  return (
    <>
      <TableRow>
        <TableCell>
          <Button onClick={toggleCollapse}>
            {isCollapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          </Button>
        </TableCell>
        <TableCell>{new Date(date.date).toLocaleDateString()}</TableCell>
        <TableCell>
          <Chip label={date.pending_arrangements.length} />
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell colSpan={3} style={{ paddingBottom: 0, paddingTop: 0, paddingLeft: 40 }}>
          <Collapse in={!isCollapsed} timeout="auto" unmountOnExit>
            <Box>
              {date.pending_arrangements.map((arrangement) => (
                <EmployeeRow
                  key={arrangement.arrangement_id}
                  request={arrangement}
                  openDocumentDialog={openDocumentDialog}
                  handleRequestAction={handleRequestAction}
                />
              ))}
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

export default DateRow;
