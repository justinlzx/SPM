import React from "react";
import { Dialog, DialogTitle, DialogContent, DialogActions, List, ListItem, Link, Button } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

type DocumentDialogProps = {
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
};

const DocumentDialog: React.FC<DocumentDialogProps> = ({ isOpen, documents, onClose }) => (
  <Dialog open={isOpen} onClose={onClose} fullWidth>
    <DialogTitle>
      Supporting Documents
      <DialogActions>
        <Button onClick={onClose}>
          <CloseIcon />
        </Button>
      </DialogActions>
    </DialogTitle>
    <DialogContent>
      <List>
        {documents.map((doc, idx) => (
          <ListItem key={idx}>
            <Link href={doc} target="_blank" rel="noopener noreferrer">
              Document {idx + 1}
            </Link>
          </ListItem>
        ))}
      </List>
    </DialogContent>
  </Dialog>
);

export default DocumentDialog;
