import { useNavigate } from "react-router-dom";
import { PendingRequests } from "./PendingRequests";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { Button } from "@mui/material";

export const TeamPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  if (!user) {
    navigate("/login");
  }

  const handleNominateManager = () => {
    navigate("/delegate"); 
  }

  return (
    <div>
      <PendingRequests />

      { (user?.role === 1 || user?.role === 3) && (
        <Button 
          variant="outlined" 
          color="primary"
          sx={{ ml: 3 }}
          onClick={handleNominateManager}
        >
          Go to Manager Delegation
        </Button>
      )}
    </div>
  );
};