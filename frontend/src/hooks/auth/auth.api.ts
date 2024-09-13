import axios from "axios";
import qs from "qs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const login = async (credentials: {
  username: string;
  password: string;
}) => {
  console.log(credentials.username, credentials.password);
  const response = await axios.post(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: qs.stringify(credentials),
  });

  console.log("response:", response);

  if (!response) {
    throw new Error("Login failed");
  }

  return response.data;
};
