import { useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { useMutation } from '@tanstack/react-query';
import { UserContext } from '../../context/UserContextProvider';
import { login } from './auth.utils';

type Credentials = {
  username: string;
  password: string;
};

export type TLoginResponse = {
  username: string;
  role: string;
};

export const useAuth = () => {
  const navigate = useNavigate();
  const { setUser } = useContext(UserContext);

  return useMutation<TLoginResponse, Error, Credentials>({
    mutationFn: login,
    onSuccess: (response) => {
      // Handle successful login
      console.log("Login successful");

      const { username, role } = response;

      setUser({ username, role });
      // Redirect to dashboard or home page
      navigate("/");
    },
    onError: (error) => {
      // Handle login error
      console.error("Login failed", error);
      // You might want to show an error message to the user
    },
  });
};