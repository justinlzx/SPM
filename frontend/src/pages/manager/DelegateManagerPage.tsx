import { useNavigate } from "react-router-dom";
import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { PendingDelegations } from "./PendingDelegations";
import { SendDelegation} from "./SendDelegation";


export const DelegateManagerPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  if (!user) {
    navigate("/login");
  }

  const handleOpenModal = () => {

  }

  return (
    <div>
      <PendingDelegations />
      <SendDelegation/>
    </div>
  );
};