import axios from "axios";
import qs from "qs";
import { TLoginResponse } from "./auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const AUTH_LOCAL_STORAGE_KEYS = {
  JWT: "jwt_access_token",
  EMAIL: "user",
  ROLE: "role",
  ID: "id",
  POSITION: "position",
  DEPT: "dept"
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

    const { access_token: accessToken, employee_info: {
      staff_id: id,
      role,
      position,
      department: dept
    } } = response.data.data;

    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.JWT, accessToken);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.EMAIL, email);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.ROLE, role.toString());
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.ID, id.toString());
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.POSITION, position);
    localStorage.setItem(AUTH_LOCAL_STORAGE_KEYS.DEPT, dept);
    axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`;

    return {
      email,
      role: Number(role),
      id: Number(id),
      position,
      dept
    };
  } catch {
    throw new Error("Login failed");
  }
};

export const logout = () => {
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.JWT);
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.EMAIL);
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.ROLE)
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.ID)
  localStorage.removeItem(AUTH_LOCAL_STORAGE_KEYS.POSITION)
  delete axios.defaults.headers.common.Authorization;
};