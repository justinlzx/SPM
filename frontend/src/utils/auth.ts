import axios from "axios";
import { TUser } from "../context/UserContextProvider";

export const AUTH_LOCAL_STORAGE_KEYS = {
  JWT: "jwt_access_token",
  USER: "user",
};

export const login = async (
  username: string,
  password: string,
  setUser: React.Dispatch<React.SetStateAction<TUser | undefined>>,
) => {
  return await axios
    .post(process.env.REACT_APP_AUTH_URL + "/api/auth/access/login", {
      username,
      password,
    })
    .then(async (res) => {
      const accessToken = res.data.data.tokens.access_token;
      localStorage.setItem(
        AUTH_LOCAL_STORAGE_KEYS.USER,
        JSON.stringify({ username: res.data.data.username }),
      );
      // setUser({ username: res.data.data.username});
      localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.JWT, accessToken);
      axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
      return res;
    })
    .catch((err) => {
      logout();
      throw err;
    });
};

export const logout = () => {
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.JWT);
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.USER);
  delete axios.defaults.headers.common.Authorization;
};
