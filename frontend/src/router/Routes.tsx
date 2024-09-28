import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/login-signup/LoginPage";
import { SignUpPage } from "../pages/login-signup/SignUpPage";
import { App } from "../App";
import { HomePage } from "../pages/home/HomePage";
import { Layout } from "../common/Layout";
<<<<<<< Updated upstream
import  { ApplicationPage }  from "../pages/staff/ApplicationPage";
=======
import { RequestPage } from "../pages/staff/RequestPage";
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
            path: "/application",
            element: <ApplicationPage />,
          }
        ]
=======
            path: "/request",
            element: <RequestPage />,
          },
        ],
>>>>>>> Stashed changes
      },
      {
        path: "/pendingrequests",
        element: <PendingRequests />,
      },
      {
        path: "/test",
        element: <TestPage />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
