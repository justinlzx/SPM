import { useContext, useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { UserContext } from "../context/UserContextProvider";
import { Header } from "./Header";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";

export const Layout = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  // Authentication check for all pages using this layout
  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <Box
        sx={{
          width: 250,
          backgroundColor: "#f5f5f5",
          padding: 2,
          boxShadow: "2px 0 5px rgba(0,0,0,0.1)",
        }}
      >
        <Typography variant="h6" gutterBottom>
          All-in-One
        </Typography>
        <Box mt={2}>
          <Button fullWidth>Notifications</Button>
          <Button fullWidth>My Team</Button>
          <Button fullWidth>My WFH Schedule</Button>
          <Button fullWidth>Settings</Button>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <Header />
        <Box sx={{ flexGrow: 1, p: 3, overflowY: "auto" }}>
          <Outlet /> {/* Render the child content here */}
        </Box>
      </Box>
    </Box>
  );
};
