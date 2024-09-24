import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { HomePage } from "../pages/home/HomePage";
import  ApplicationPage  from "../pages/staff/ApplicationPage";

type routesProps = {
  path: string;
  element: JSX.Element;
  children?: routesProps[];
};

const routes: routesProps[] = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/sign-up",
        element: <SignUpPage />,
      },
      {
        path: "/home",
        element: <HomePage />,
      },
      {
        path: "/application", 
        element: <ApplicationPage />, 
      }
    ],
  },
];

export const router = createBrowserRouter(routes);
