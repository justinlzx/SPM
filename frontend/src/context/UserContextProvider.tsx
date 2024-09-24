import axios from "axios";
import { createContext, useEffect, useState } from "react";
import {
  AUTH_LOCAL_STORAGE_KEYS,
  logout as logoutUtil,
} from "../hooks/auth/auth.utils";
import { login } from "../hooks/auth/auth.utils";

export type TUser = {
  username: string;
  role: string;
};

type TAuthenticationContext = { user?: TUser } & {
  login: typeof login;
  logout: typeof logoutUtil;
  setUser: React.Dispatch<React.SetStateAction<TUser | undefined>>;
};

export const UserContext = createContext<TAuthenticationContext>({
  login,
  logout: logoutUtil,
  setUser: () => {},
});

type Props = {
  children: string | JSX.Element | JSX.Element[];
};

export const UserContextProvider = ({ children }: Props) => {
  const [user, setUser] = useState<TUser | undefined>();

  const logout = () => {
    logoutUtil();
    setUser(undefined);
  };

  useEffect(() => {
    // try {
    //   const accessToken = localStorage.getItem(AUTH_LOCAL_STORAGE_KEYS.JWT);

    //   const userData = JSON.parse(
    //     localStorage.getItem(AUTH_LOCAL_STORAGE_KEYS.USER) || ""
    //   );
    //   axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
    //   if (userData) {
    //     setUser(userData);
    //   }
    // } catch {
    //   setUser(undefined);
    // }
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser, login, logout }}>
      {children}
    </UserContext.Provider>
  );
};
