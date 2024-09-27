import { createBrowserRouter, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { Layout } from "../common/Layout";
import { ApplicationPage } from "../pages/staff/ApplicationPage";
import { StaffHomePage } from "../pages/staff/StaffHomePage";

import { TeamPage } from "../pages/team/TeamPage";

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
            path: "/application",
            element: <ApplicationPage />,
          },
          {
            path: "/team",
            element: <TeamPage />,
          },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
