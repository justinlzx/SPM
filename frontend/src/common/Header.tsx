import * as React from "react";
import logo from "../logo.svg";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import CssBaseline from "@mui/material/CssBaseline";
import IconButton from "@mui/material/IconButton";
import MenuIcon from "@mui/icons-material/Menu";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { useContext } from "react";
import { UserContext } from "../context/UserContextProvider";
import { Sidebar } from "./Sidebar";
import "@fontsource/poppins";

const drawerWidth = 240;

interface Props {
  window?: () => Window;
}

export const Header = ({ window }: Props) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const { user, logout } = useContext(UserContext);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const container = window !== undefined ? () => window().document.body : undefined;

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: "white",
          color: "black",
          boxShadow: "none",
          borderBottom: "1px solid #e0e0e0",
          pb:1
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: "none" } }}
          >
            <MenuIcon />
          </IconButton>
          <img src={logo} alt="logo" style={{ height: "40px", width: "40px" }} />
          <Typography variant="h6" noWrap component="div">
            All-in-One
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Button onClick={logout} color="inherit">
            Log Out
          </Button>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Sidebar mobileOpen={mobileOpen} handleDrawerToggle={handleDrawerToggle} container={container} />
        <Toolbar />
        {/* Content goes here */}
      </Box>
    </Box>
  );
};

export default Header;
