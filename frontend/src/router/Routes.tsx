import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { Layout } from "../common/Layout";
import { CreateWfhRequest } from "../components/forms/CreateWfhRequest";
import { ReviewRequests } from "../pages/manager/ReviewRequests";
import { HomePage } from "../pages/staff/HomePage";
import { TeamPage } from "../pages/team/TeamPage";
import { Settings } from "../pages/staff/Settings";
import { MyWfhSchedulePage } from "../pages/staff/MyWfhSchedulePage";


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
            element: <CreateWfhRequest />,
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
            path: "/settings",
            element: <Settings />,
          },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
