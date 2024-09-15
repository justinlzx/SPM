import { useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { useMutation } from '@tanstack/react-query';
import { UserContext } from '../../context/UserContextProvider';
import { login, signUp } from './auth.utils';

type TCredentials = {
  username: string;
  password: string;
};

type TSignupCredentials = TCredentials & {
  email: string;
  role: string;
};

export type TLoginResponse = {
  username: string;
  role: string;
};

export const useLogin = () => {
  const navigate = useNavigate();
  const { setUser } = useContext(UserContext);

  return useMutation<TLoginResponse, Error, TCredentials>({
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

export const useSignup = () => {
  const navigate = useNavigate();

  return useMutation<void, Error, TSignupCredentials>({
    mutationFn: signUp,
    onSuccess: async () => {
      // Handle successful signup
      console.log("Signup successful");
      // Redirect to login page
      navigate("/login");
    },
    onError: (error) => {
      // Handle signup error
      console.error("Signup failed", error);
    },
  });
};