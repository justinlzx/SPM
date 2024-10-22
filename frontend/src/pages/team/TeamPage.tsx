import { useNavigate } from "react-router-dom";
import { PendingRequests } from "./PendingRequests";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import RequestList from '../../pages/team/RequestList';


export const TeamPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  if (!user) {
    navigate("/login");
  }

  return (
    <div>
      <PendingRequests />
      <RequestList/>
    </div>
  );
};