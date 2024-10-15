import { useNavigate } from "react-router-dom";
import { PendingRequests } from "./PendingRequests";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";

export const TeamPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  if (!user) {
    navigate("/login");
  }

  return (
    <div>
      approved requests for the entire team should go here
    </div>
  );
};