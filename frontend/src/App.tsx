import "./App.css";
import { useContext, useEffect } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { UserContext } from "./context/UserContextProvider";
import { AppContext } from "./context/AppContextProvider";
import { SnackBarComponent as SnackBar } from "./common/SnackBar";
import { Outlet, useNavigate } from "react-router-dom";
import { useHealthCheck } from "./hooks/auth/health/health";


const theme = createTheme({
  typography: {
    fontFamily: 'Poppins, sans-serif',
  },
});



export const App = () => {
  const { alertStatus, showSnackbar, snackbarMessage, handleCloseSnackBar } =
    useContext(AppContext);

  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const { mutate } = useHealthCheck();

  useEffect(() => {
    if (user === undefined) {
      navigate("/home");
      return;
    }
  }, [user, navigate]);

  useEffect(() => {
    mutate();
  }, [mutate]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline/>
      <div>
        {alertStatus !== undefined && (
          <SnackBar
            alertStatus={alertStatus}
            showSnackbar={showSnackbar}
            snackbarMessage={snackbarMessage}
            handleCloseSnackBar={handleCloseSnackBar}
          />
        )}
        <Outlet />
      </div>
    </ThemeProvider>
  );
};
