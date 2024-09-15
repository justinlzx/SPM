import React, { useContext } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import reportWebVitals from "./reportWebVitals";
import { RouterProvider } from "react-router-dom";
import { router } from "./router/Routes";
import { UserContextProvider } from "./context/UserContextProvider";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppContext, AppContextProvider } from "./context/AppContextProvider";
import { SnackBarComponent as SnackBar } from "./common/SnackBar";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);



const queryClient = new QueryClient();
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppContextProvider>
        <UserContextProvider>
          <RouterProvider router={router} />
        </UserContextProvider>
      </AppContextProvider>
    </QueryClientProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
