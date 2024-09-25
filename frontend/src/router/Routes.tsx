import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { HomePage } from "../pages/home/HomePage";
import PendingRequests from '../pages/pendingrequests/Pendingrequests'; 

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
        path: "/pendingrequests",
        element: <PendingRequests />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
