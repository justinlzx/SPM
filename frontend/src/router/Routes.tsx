import { createBrowserRouter, RouteObject } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { Layout } from "../common/Layout";
import { CreateWfhRequestPage } from "../pages/staff/CreateWfhRequest";
import { ReviewRequests } from "../pages/manager/ReviewRequests";
import { HomePage } from "../pages/staff/HomePage";
import { TeamPage } from "../pages/team/TeamPage";
import { MyWfhSchedulePage } from "../pages/staff/MyWfhSchedulePage";
import { DelegateManagerPage } from "../pages/manager/DelegateManagerPage";
import { DepartmentOverviewPage } from "../pages/hr/DepartmentOverviewPage";


const routes: RouteObject[] = [
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
            index: true, 
            element: <HomePage />,
          },
          {
            path: "home",
            element: <HomePage />,
          },
          {
            path: "create-request",
            element: <CreateWfhRequestPage />,
          },
          {
            path: "review-requests",
            element: <ReviewRequests />,
          },
          {
            path: "team",
            element: <TeamPage />,
          },
          {
            path: "wfh-schedule",
            element: <MyWfhSchedulePage />,
          },
          {
            path: "delegate",
            element: <DelegateManagerPage />,
          },
          {
            path: "department-overview",
            element: <DepartmentOverviewPage />,
          },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
