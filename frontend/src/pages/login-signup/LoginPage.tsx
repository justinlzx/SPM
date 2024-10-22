import { useState } from "react";
import logo from "../../logo.svg";
import { IconButton, Input, InputAdornment, InputLabel } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import { useLogin } from "../../hooks/auth/auth";
import { VisibilityOff, Visibility } from "@mui/icons-material";

export const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null); // To store error messages
  const navigate = useNavigate(); // Corrected typo

  const { mutate } = useLogin();

  const [showPassword, setShowPassword] = useState(false);
  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const handleMouseDownPassword = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
  };

  const handleLogin = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setError(null); // Reset error message on new login attempt

    mutate(
      { email, password },
      {
        onSuccess: () => {
          setIsLoggingIn(false);
          navigate("/home");
        },
        onError: (error: any) => {
          setIsLoggingIn(false);
          setError("Invalid email or password. Please try again.");
        },
      }
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-white">
      <div className="w-full max-w-sm bg-transparent p-8">
        <div className="mb-6 flex justify-center py-5">
          <img src={logo} alt="login-logo" />
        </div>

        {/* Form */}
        <form className="space-y-6" onSubmit={handleLogin}>
          {/* Email input */}
          <InputLabel htmlFor="email" variant="outlined">
            Email
          </InputLabel>
          <Input
            id="email"
            data-cy= "email"
            type="email"
            placeholder="Enter Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-300 p-3"
          />

          {/* Password input */}
          <InputLabel htmlFor="password" variant="outlined">
            Password
          </InputLabel>
          <Input
            data-cy="password"
            id="password"
            type={showPassword ? "text" : "password"}
            value={password}
            className="w-full p-3 rounded-md border border-gray-300"
            placeholder="Enter Password"
            disableUnderline
            endAdornment={
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={handleClickShowPassword}
                  onMouseDown={handleMouseDownPassword}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            }
            onChange={(e) => setPassword(e.target.value)}
          />

          {/* Error message */}
          {error && <div className="text-red-500 text-sm mt-2">{error}</div>}

          {/* Submit button */}
          <div>
            <button data-cy = "submit"
              type="submit"
              className={`${
                isLoggingIn ? "opacity-50" : ""
              } w-full rounded-lg bg-blue-950 px-4 py-2 text-white`}
              disabled={isLoggingIn}
            >
              {isLoggingIn ? "Logging in..." : "LOGIN"}
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
