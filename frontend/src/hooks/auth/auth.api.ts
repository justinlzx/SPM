import axios from "axios";
import qs from "qs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const login = async (credentials: {
  username: string;
  password: string;
}) => {
  const response = await axios.post(
    `${BACKEND_URL}/auth/login`,
    qs.stringify(credentials),
    {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }
  );

  if (!response) {
    throw new Error("Login failed");
  }

  return response.data;
};