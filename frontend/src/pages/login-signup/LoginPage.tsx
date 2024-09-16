import { useState } from "react";
import logo from "../../logo.svg";
import { IconButton, Input, InputAdornment, InputLabel } from "@mui/material";
import { Link } from "react-router-dom";
import { useLogin } from "../../hooks/auth/auth";
import { VisibilityOff, Visibility } from "@mui/icons-material";

export const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const { mutate } = useLogin();

  const [showPassword, setShowPassword] = useState(false);

  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const handleMouseDownPassword = (
    event: React.MouseEvent<HTMLButtonElement>
  ) => {
    event.preventDefault();
  };

  const handleMouseUpPassword = (
    event: React.MouseEvent<HTMLButtonElement>
  ) => {
    event.preventDefault();
  };

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
          <InputLabel htmlFor="filled-adornment-password" variant="outlined">
            Username
          </InputLabel>
          <Input
            type="username"
            placeholder="Enter Username"
            value={username}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setUsername(e.target.value)
            }
            className="w-full rounded-lg border border-gray-300 p-3"
          />

          {/* Password input */}
          <InputLabel htmlFor="filled-adornment-password" variant="outlined">
            Password
          </InputLabel>
          <Input
            id="filled-adornment-password"
            type={showPassword ? "text" : "password"}
            value={password}
            className="w-full p-3 rounded-md border border-gray-300"
            placeholder="Enter Password"
            disableUnderline={true}
            endAdornment={
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={handleClickShowPassword}
                  onMouseDown={handleMouseDownPassword}
                  onMouseUp={handleMouseUpPassword}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            }
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setPassword(e.target.value)
            }
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