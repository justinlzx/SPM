import { useNavigate } from "react-router-dom";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { Button } from "@mui/material";

export const DelegateButton = () => {
    const { user } = useContext(UserContext);
    const navigate = useNavigate();

    const handleNominateManager = () => {
        navigate("/delegate"); 
    }
    return (
        <>
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
        </>
    );
    };