import { useNavigate } from "react-router-dom";
import { PendingRequests } from "./PendingRequests";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { RequestList } from "./RequestList";
import { Box, Typography } from "@mui/material";
import { DelegateButton } from "../manager/DelegateButton";
import PeopleOutlineIcon from '@mui/icons-material/PeopleOutline';


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
      <RequestList/>
      { (user?.role === 1 || user?.role === 3) && (
         <Box 
         display="flex" 
         alignItems="center" 
         justifyContent="space-between" 
         sx={{ my: 4, gap: 2, p: 2, border: '1px solid lightgrey', borderRadius: 1 }}
       >
         <Box display="flex" alignItems="center" gap={2}>
           <PeopleOutlineIcon />
           <Typography variant="body2">
             Remember to delegate a peer manager when you are on leave or unavailable.
           </Typography>
         </Box>
         <DelegateButton />
       </Box>
      )}
    </div>
  );
};