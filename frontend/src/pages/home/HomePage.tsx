import { useContext, useEffect } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { Outlet, useNavigate } from "react-router-dom";
import { Header } from "../../common/Header";

export const HomePage = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (user === undefined) {
      navigate("/login");
    }
  }, [user, navigate]);

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <Header/>
      <Outlet />
    </div>
  );
};

export default HomePage; 
