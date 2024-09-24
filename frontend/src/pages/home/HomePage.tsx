import { useContext, useEffect } from "react";
import { UserContext } from "../../context/UserContextProvider";
import logo from "../../logo.svg";
import { Outlet, useNavigate } from "react-router-dom";

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

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  return (
    <div>
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>Hello {user!.email}</p>
        <button onClick={() => handleNavigate("/test")}>Go to test</button>
      </header>
      <Outlet />
    </div>
  );
};
