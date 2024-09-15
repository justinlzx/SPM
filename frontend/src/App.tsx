import "./App.css";
import { useContext, useEffect } from "react";
import { UserContext } from "./context/UserContextProvider";
import { LoginPage } from "./pages/login-signup/LoginPage";
import { AppContext } from "./context/AppContextProvider";
import { SnackBarComponent as SnackBar } from "./common/SnackBar";
import { Outlet, useNavigate } from "react-router-dom";

export const App = () => {
  const { alertStatus, showSnackbar, snackbarMessage, handleCloseSnackBar } =
    useContext(AppContext);

  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

function App() {
  return (
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
  );
}

export default App;
