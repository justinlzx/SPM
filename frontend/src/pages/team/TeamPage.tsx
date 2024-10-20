import { useNavigate } from "react-router-dom";
import { PendingRequests } from "./PendingRequests";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { NominateManager } from "./NominateManager";

export const TeamPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  if (!user) {
    navigate("/login");
  }

  return (
    <div>
      <NominateManager />
      <PendingRequests />
    </div>
  );
};