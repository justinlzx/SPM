import axios from "axios";
import qs from "qs";
import { TLoginResponse } from "./auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const AUTH_LOCAL_STORAGE_KEYS = {
  JWT: "jwt_access_token",
  EMAIL: "user",
  ROLE: "role",
};

export const signUp = async (credentials: {
  username: string;
  email: string;
  password: string;
  role: number;
}): Promise<void> => {
  try {
    await axios.post(
      `${BACKEND_URL}/auth/register`,
      qs.stringify(credentials),
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    );

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

    const { access_token: accessToken } = response.data.data;
    // TODO: remove this hardcode when the backend is ready
    const role = 1
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.JWT, accessToken);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.EMAIL, email);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.ROLE, role.toString());

    axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;

    return {
      email,
      role: Number(role)
    };
  } catch (error) {
    throw new Error("Login failed");
  }
};

export const logout = () => {
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.JWT);
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.EMAIL);
  delete axios.defaults.headers.common.Authorization;
};