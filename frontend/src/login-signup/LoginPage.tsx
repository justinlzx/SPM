import { useState } from "react";
import logo from "../logo.svg";
import { Input } from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/auth/auth";

export const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const { mutate } = useAuth();

  const handleLogin = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    mutate({ username, password });
    setIsLoggingIn(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-white">
      <div className="w-full max-w-sm bg-transparent p-8">
        {/* TODO: replace with product logo */}
        <div className="mb-6 flex justify-center py-5 animate-spin">
          <img src={logo} />
        </div>

        {/* Form */}
        <form className="space-y-6" onSubmit={handleLogin}>
          {/* Username input */}
          <Input
            type="username"
            placeholder="Username"
            value={username}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setUsername(e.target.value)
            }
            className="w-full rounded-lg border border-gray-300 p-3"
          />

          {/* Password input */}
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setPassword(e.target.value)
            }
            className="w-full rounded-lg border border-gray-300 p-3"
          />

          {/* Submit button */}
          <div>
            <button
              type="submit"
              className={`${
                isLoggingIn && "opacity-50"
              } w-full rounded-lg bg-blue-950 px-4 py-2 text-white`}
              disabled={isLoggingIn}
            >
              LOGIN
            </button>
          </div>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Do not have an account yet?{" "}
          <Link to={"/sign-up"} className="text-blue-950 underline">
            Sign up here
          </Link>
          .
        </div>
      </div>
    </div>
  );
};
