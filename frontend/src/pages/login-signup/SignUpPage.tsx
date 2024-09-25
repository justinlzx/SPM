import { useContext, useState } from "react";
import {
  IconButton,
  Input,
  InputAdornment,
  InputLabel,
  MenuItem,
  TextField,
} from "@mui/material";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import { Link, useNavigate } from "react-router-dom";
import React from "react";
import logo from "../../logo.svg";
import { useSignup } from "../../hooks/auth/auth";
import { AppContext } from "../../context/AppContextProvider";
import { AlertStatus } from "../../common/SnackBar";

enum Roles {
  Select = "Select role",
  Staff = "Staff",
  HR = "HR",
  Manager = "Manager",
}

export const SignUpPage = () => {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(0);

  const [showPassword, setShowPassword] = useState(true);

  const navigate = useNavigate();

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

  const { mutate } = useSignup();
  const { setAlertStatus, setShowSnackbar, setSnackbarMessage } =
    useContext(AppContext);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission logic
    mutate(
      {
        email,
        username,
        password,
        role,
      },
      {
        onSuccess: () => {
          setAlertStatus(AlertStatus.Success);
          setShowSnackbar(true);
          setSnackbarMessage("Signup successful");
          navigate("/login");
        },
        onError: (error: any) => {
          setAlertStatus(AlertStatus.Error);
          setShowSnackbar(true);
          if (error.message) {
            setSnackbarMessage(error.message);
          }
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="w-full max-w-sm p-8 bg-transparent">
        {/* TODO: replace with product logo */}
        <div className="mb-6 flex justify-center py-5 animate-spin">
          <img src={logo} />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* email input */}
          <InputLabel htmlFor="outlined-adornment-email" variant="outlined">
            Email
          </InputLabel>
          <Input
            type="email"
            placeholder="Enter email"
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setEmail(e.target.value)
            }
            className="w-full p-3 rounded-lg border border-gray-300"
            color="primary"
            disableUnderline={true}
            required
          />
          {/* Username input */}
          <InputLabel htmlFor="filled-adornment-password" variant="outlined">
            Username
          </InputLabel>
          <Input
            type="username"
            placeholder="Enter username"
            value={username}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setUsername(e.target.value)
            }
            className="w-full p-3 rounded-lg border border-gray-300"
            disableUnderline={true}
            required
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
            placeholder="Enter password"
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

          {/* Role input */}
          <InputLabel variant="outlined">Role</InputLabel>
          <TextField
            sx={{
              "& .MuiSelect-select span::before": {
                content: "'Select Roles'",
                color: "grey",
              },
            }}
            select
            value={role}
            onChange={(e) => {
              const selectedRole = e.target.value as Roles;
              const roleIndex = Object.values(Roles).indexOf(selectedRole);
              setRole(roleIndex);
              console.log("Selected role index:", roleIndex); // You can use this index as needed
            }}
            className="w-full p-3 rounded-md border border-gray-300"
          >
            {Object.values(Roles).map((role) => (
              <MenuItem
                key={role}
                value={role}
                disabled={role === Roles.Select}
              >
                {role}
              </MenuItem>
            ))}
          </TextField>

          {/* Submit button */}
          <div>
            <button
              type="submit"
              className="w-full bg-blue-950 text-white py-2 px-4 rounded-lg"
            >
              SIGN UP
            </button>
          </div>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-950 underline">
            Log in here
          </Link>
          .
        </div>
      </div>
    </div>
  );
};
