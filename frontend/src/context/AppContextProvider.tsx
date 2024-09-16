import { SnackbarCloseReason } from "@mui/material/Snackbar/Snackbar";
import { createContext, useState } from "react";

export type TSnackBar = {
  showSnackbar: boolean;
  setShowSnackbar: React.Dispatch<React.SetStateAction<boolean>>;
  alertStatus: "error" | "success" | "info" | "warning";
  setAlertStatus: React.Dispatch<
    React.SetStateAction<"error" | "success" | "info" | "warning">
  >;
  snackbarMessage: string;
  setSnackbarMessage: React.Dispatch<React.SetStateAction<string>>;
  handleCloseSnackBar: (
    event: React.SyntheticEvent | Event,
    reason?: SnackbarCloseReason
  ) => void;
};

type TAppContext = TSnackBar;

export const AppContext = createContext<TAppContext>({
  showSnackbar: false,
  setShowSnackbar: () => {},
  alertStatus: "info",
  setAlertStatus: () => {},
  snackbarMessage: "",
  setSnackbarMessage: () => {},
  handleCloseSnackBar: () => {},
});

type Props = {
  children: string | JSX.Element | JSX.Element[];
};

export const AppContextProvider = ({ children }: Props) => {
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [alertStatus, setAlertStatus] = useState<
    "error" | "success" | "info" | "warning"
  >("info");
  const [snackbarMessage, setSnackbarMessage] = useState("");

  const handleCloseSnackBar = (
    event: React.SyntheticEvent | Event,
    reason?: SnackbarCloseReason
  ) => {
    if (reason === "clickaway") {
      return;
    }

    setShowSnackbar(false);
  };

  return (
    <AppContext.Provider
      value={{
        showSnackbar,
        setShowSnackbar,
        alertStatus,
        setAlertStatus,
        snackbarMessage,
        setSnackbarMessage,
        handleCloseSnackBar,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};
