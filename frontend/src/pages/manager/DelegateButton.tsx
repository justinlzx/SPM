import { useNavigate } from "react-router-dom";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { Button } from "@mui/material";
import ManageAccountsIcon from "@mui/icons-material/ManageAccounts";

export const DelegateButton = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  const handleNominateManager = () => {
    navigate("/delegate");
  };
  return (
    <>
      {((user?.role === 1 && user.position === "Director") ||
        user?.role === 3) && (
        <Button
          variant="outlined"
          color="primary"
          sx={{ ml: 3 }}
          onClick={handleNominateManager}
        >
          <ManageAccountsIcon />
          Go to Manager Delegation
        </Button>
      )}
    </>
  );
};
