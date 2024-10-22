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
    fontSize: 13,
    fontFamily: 'Poppins, sans-serif',
  },
  palette: {
    primary: {
      main: '#00007B', 
      light: '#3399ff',
      dark: '#002080',
    },
    secondary: {
      main: '#262626',
      light: '#4d4d4d',
      dark: '#1f1f1f',
    },
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
      navigate("/login");
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
