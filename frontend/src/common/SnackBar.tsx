import { Alert } from "@mui/material";
import Snackbar from "@mui/material/Snackbar";
import { TSnackBar as TSnackBarContext } from "../context/AppContextProvider";

type TSnackBar = Partial<TSnackBarContext>;

export enum AlertStatus {
  Error = "error",
  Success = "success",
  Info = "info",
  Warning = "warning",
}

export const SnackBarComponent = ({
  showSnackbar,
  handleCloseSnackBar,
  alertStatus,
  snackbarMessage,
}: TSnackBar) => {
  return (
    <Snackbar
      open={showSnackbar}
      autoHideDuration={3000}
      onClose={handleCloseSnackBar}
      anchorOrigin={{ vertical: "top", horizontal: "center" }}  // Set the position to top center
    >
      <Alert
        onClose={handleCloseSnackBar}
        severity={alertStatus}
        variant="filled"
        sx={{ width: "100%" }}
      >
        {snackbarMessage}
      </Alert>
    </Snackbar>
  );
};
