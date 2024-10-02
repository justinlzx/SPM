import { createBrowserRouter, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { Layout } from "../common/Layout";
import { RequestPage } from "../pages/staff/RequestPage";
import { StaffHomePage } from "../pages/staff/StaffHomePage";

import { TeamPage } from "../pages/team/TeamPage";
import { RequestPage } from "../pages/staff/RequestPage";

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
            path: "/request",
            element: <RequestPage />,
          },
          {
            path: "/team",
            element: <TeamPage />,
          },
          {
            path: "/requests", 
            element: <RequestPage />
          }
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
