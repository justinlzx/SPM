import { useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { useMutation } from '@tanstack/react-query';
import { UserContext } from '../../context/UserContextProvider';
import { login, signUp } from './auth.utils';

type TCredentials = {
  email: string;
  password: string;
};

type TSignupCredentials = TCredentials & {
  username: string;
  role: number;
};

export type TLoginResponse = {
  email: string;
  role: number;
  id: number;
};

export const useLogin = () => {
  const navigate = useNavigate();
  const { setUser } = useContext(UserContext);

  return useMutation<TLoginResponse, Error, TCredentials>({
    mutationFn: login,
    onSuccess: (response) => {
      // Handle successful login
      console.log("Login successful");

      const { email, role, id } = response;

      setUser({ email, role, id });
      // Redirect to dashboard or home page
      navigate("/home");
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