import { useContext, useEffect } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { useNavigate } from "react-router-dom";


export const HomePage = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    // if (user === undefined) {
    //   navigate("/login");
    // }
  }, [user, navigate]);

  // if (!user) {
  //   return <div>Loading...</div>;
  // }

  const handleNavigate = (path: string) => {
    navigate(path);
  }

  return (
    <div>
      
      
      <button 
        onClick={() => handleNavigate("/test")} 
        style={{ backgroundColor: "black", color: "white" }}
      >
        Go to test
      </button>
    </div>
  );
};

export default HomePage; 
