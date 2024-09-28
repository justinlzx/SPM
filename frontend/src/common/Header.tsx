import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import CssBaseline from "@mui/material/CssBaseline";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import InboxIcon from "@mui/icons-material/MoveToInbox";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import TeamIcon from "@mui/icons-material/Group";
import WfhScheduleIcon from "@mui/icons-material/WorkOutline";
import SettingsIcon from "@mui/icons-material/Settings";
import MenuIcon from "@mui/icons-material/Menu";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import "@fontsource/poppins"; // Defaults to weight 400
import Button from "@mui/material/Button";
import { useContext } from "react";
import { UserContext } from "../context/UserContextProvider";
import { useNavigate } from "react-router-dom";
import { AppContext } from "../context/AppContextProvider";

const drawerWidth = 240;

interface Props {
  window?: () => Window;
}

export enum sideBarLabels {
  Requests = "Requests",
  MyTeam = "My Team",
  MyWFHSchedule = "My WFH Schedule",
  Settings = "Settings",
}

const sideBarItems: {
  text: string;
  icon: JSX.Element;
  route?: string; // TODO: add route property when it is done
}[] = [
  {
    text: sideBarLabels.Requests,
    icon: <InboxIcon />,
    route: "/application",
  },
  { text: sideBarLabels.MyTeam, icon: <TeamIcon />, route: "/team" },
  { text: sideBarLabels.MyWFHSchedule, icon: <WfhScheduleIcon /> },
  { text: sideBarLabels.Settings, icon: <SettingsIcon /> },
];

export const Header = ({ window }: Props) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const { activeTab, setActiveTab } = useContext(AppContext);
  const { logout } = useContext(UserContext);
  const navigate = useNavigate();

  const handleButtonClick = (route: string) => {
    setActiveTab(sideBarItems.findIndex((item) => item.route === route));
    navigate(route);
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%" }}>
      <Toolbar />
      <Divider />
      <List>
        {sideBarItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              sx={{
                textAlign: "left",
                alignItems: "left",
                backgroundColor:
                  activeTab === sideBarItems.indexOf(item)
                    ? "#e0e0e0"
                    : "white",
              }}
              onClick={() => handleButtonClick(item.route || "")}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  const container =
    window !== undefined ? () => window().document.body : undefined;

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
          <Typography variant="h6" noWrap component="div">
            All-in-One
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Button onClick={logout} color="inherit">
            Log Out
          </Button>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          container={container}
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: "block", sm: "block", md: "none" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
              bgcolor: "#f5f5f5",
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: "none", sm: "none", md: "block" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
              bgcolor: "#f5f5f5",
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {/* Add your content here */}
      </Box>
    </Box>
  );
};

export default Header;
