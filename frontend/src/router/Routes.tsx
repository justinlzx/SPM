import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../login-signup/LoginPage";
import { SignUpPage } from "../login-signup/SignUpPage";
import { App } from "../App";

type routesProps = {
  path: string;
  element: JSX.Element;
  children?: routesProps[];
};

const routes: routesProps[] = [
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
    element: <App />,
    children: [],
  },
];

export const router = createBrowserRouter(routes);
