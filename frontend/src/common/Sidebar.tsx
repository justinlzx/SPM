import * as React from "react";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Toolbar from "@mui/material/Toolbar";
import { useContext } from "react";
import { AppContext } from "../context/AppContextProvider";
import { useNavigate } from "react-router-dom";
import InboxIcon from "@mui/icons-material/MoveToInbox";
import SpaceDashboardIcon from '@mui/icons-material/SpaceDashboard';
import TeamIcon from "@mui/icons-material/Group";
import WfhScheduleIcon from '@mui/icons-material/CalendarMonth';
import SettingsIcon from "@mui/icons-material/Settings";

// Define sideBarLabels here since it's only used by the Sidebar component
enum sideBarLabels {
  Dashboard = "Dashboard",
  Requests = "Requests",
  MyTeam = "My Team",
  MyWFHSchedule = "My WFH Schedule",
  Settings = "Settings",
  DepartmentOverview = "Department Overview",
  ReviewRequests = "Review Requests",
}

const drawerWidth = 240;

const sideBarItems = [
  { text: sideBarLabels.Dashboard, icon: <SpaceDashboardIcon />, route: "/home" },
  { text: sideBarLabels.Requests, icon: <InboxIcon />, route: "/request" },
  { text: sideBarLabels.MyTeam, icon: <TeamIcon />, route: "/team" },
  { text: sideBarLabels.MyWFHSchedule, icon: <WfhScheduleIcon />, route: "/wfh-schedule" },
  { text: sideBarLabels.Settings, icon: <SettingsIcon />, route: "/settings" },
];

interface SidebarProps {
  mobileOpen: boolean;
  handleDrawerToggle: () => void;
  container?: Element | (() => Element | null) | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, handleDrawerToggle, container }) => {
  const { activeTab, setActiveTab } = useContext(AppContext);
  const navigate = useNavigate();

  const handleButtonClick = (route: string) => {
    setActiveTab(sideBarItems.findIndex((item) => item.route === route));
    navigate(route);
  };

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%"}}>
      <Toolbar/>
      <List>
        {sideBarItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              sx={{
                textAlign: "left",
                alignItems: "left",
                backgroundColor: activeTab === sideBarItems.indexOf(item) ? "navy" : "#f5f5f5",
                color: activeTab === sideBarItems.indexOf(item) ? "white" : "inherit",
                '&:hover': {
                  backgroundColor: activeTab === sideBarItems.indexOf(item) ? "navy" : "#e0e0e0",
                }
              }}
              onClick={() => handleButtonClick(item.route || "")}
            >
              <ListItemIcon sx={{ color: activeTab === sideBarItems.indexOf(item) ? "white" : "inherit" }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      {/* Temporary Drawer for Mobile Devices */}
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
            pt:-1
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Permanent Drawer for Desktop Devices */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", sm: "none", md: "block" },
          "& .MuiDrawer-paper": {
            boxSizing: "border-box",
            width: drawerWidth,
            bgcolor: "#f5f5f5",
            pt:-1
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  );
};
