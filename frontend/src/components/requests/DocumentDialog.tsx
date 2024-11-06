import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  Link,
  Button,
} from "@mui/material";

type TDocumentDialogProps = {
  isOpen: boolean;
  documents: string[];
  onClose: () => void;
};

// DocumentDialog component for viewing supporting documents
export const DocumentDialog = ({
  isOpen,
  documents,
  onClose,
}: TDocumentDialogProps) => (
  <Dialog open={isOpen} onClose={onClose} fullWidth>
    <DialogTitle>Supporting Documents</DialogTitle>
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
              View Document
            </Link>
          </ListItem>
        ))}
      </List>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>Close</Button>
    </DialogActions>
  </Dialog>
);
