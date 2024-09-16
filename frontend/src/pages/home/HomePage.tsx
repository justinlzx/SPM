import { useContext } from "react";
import { UserContext } from "../../context/UserContextProvider";
import logo from "../../logo.svg";
import { Outlet, useNavigate } from "react-router-dom";

export const HomePage = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  if (!user) {
    navigate("/login");
  }

  return (
    <div >
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>Hello {user!.username}</p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
      <Outlet />
    </div>
  );
};