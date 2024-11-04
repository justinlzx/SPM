import { createBrowserRouter } from "react-router-dom";
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
import { RequestHistoryPage } from "../pages/hr/RequestHistory";

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
            element: <HomePage />,
          },
          {
            path: "/create-request",
            element: <CreateWfhRequestPage />,
          },
          {
            path: "/review-requests",
            element: <ReviewRequests />,
          },
          {
            path: "/team",
            element: <TeamPage />,
          },
          {
            path: "/wfh-schedule",
            element: <MyWfhSchedulePage />,
          },
          {
            path: "/delegate",
            element: <DelegateManagerPage />
          },
          {
            path: "/request-history",
            element: <RequestHistoryPage />
          }
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
