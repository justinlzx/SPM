import { createBrowserRouter, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { HomePage } from "../pages/home/HomePage";
import { Layout } from "../common/Layout";
import { ApplicationPage } from "../pages/staff/ApplicationPage";
import { TestPage } from "./TestPage";
import { StaffHomePage } from "../pages/staff/StaffHomePage";
import PendingRequests from "../pages/pendingrequests/Pendingrequests";

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
        path: "/",
        element: <Layout />,
        children: [
          {
            path: "/home",
            element: <StaffHomePage />,
          },
          {
            path: "/test",
            element: <TestPage />,
          },
          {
            path: "/application",
            element: <ApplicationPage />,
          },
        ],
      },
      {
        path: "/pendingRequests",
        element: <PendingRequests />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
