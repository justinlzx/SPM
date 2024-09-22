import axios from "axios";
import qs from "qs";
import { TLoginResponse } from "./auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const AUTH_LOCAL_STORAGE_KEYS = {
  JWT: "jwt_access_token",
  USER: "user",
  ROLE: "role",
};

export const signUp = async (credentials: {
  username: string;
  email: string;
  password: string;
  role: string;
}): Promise<void> => {
  try {
    await axios.post(
      `${BACKEND_URL}/auth/register`,
      qs.stringify(credentials),
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    );
    console.log("Signup successful");

  } catch (error: any) {
    console.log(error)
    throw new Error(error.response.data.detail);
  }
};

export const login = async (credentials: {
  email: string;
  password: string;
}): Promise<TLoginResponse> => {
  const { email } = credentials;
  
  try {
    const response = await axios.post(
      `${BACKEND_URL}/auth/login`,
      qs.stringify(credentials),
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    );

    const { access_token: accessToken, role } = response.data.data;

    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.JWT, accessToken);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.USER, email);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.ROLE, role);

    axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;

    return {
      email,
      role,
    };
  } catch (error) {
    throw new Error("Login failed");
  }
};

export const logout = () => {
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.JWT);
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.USER);
  delete axios.defaults.headers.common.Authorization;
};