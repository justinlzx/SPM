import { createBrowserRouter, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { HomePage } from "../pages/home/HomePage";
import { Layout } from "../common/Layout";
import { RequestPage } from "../pages/staff/RequestPage";
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
            path: "/request",
            element: <RequestPage />,
          }
        ]
      },
     
    ],
  },
];

export const router = createBrowserRouter(routes);
