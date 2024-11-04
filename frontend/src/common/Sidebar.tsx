// src/common/Sidebar.tsx
import * as React from "react";
import { useContext } from "react";
import { UserContext } from "../context/UserContextProvider";
import { useNavigate, useLocation } from "react-router-dom";

import InboxIcon from "@mui/icons-material/MoveToInbox";
import PostAddIcon from "@mui/icons-material/PostAdd";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Toolbar from "@mui/material/Toolbar";
import SpaceDashboardIcon from "@mui/icons-material/SpaceDashboard";
import TeamIcon from "@mui/icons-material/Group";
import WfhScheduleIcon from "@mui/icons-material/CalendarMonth";

const drawerWidth = 240;

const sideBarItems = [
  { text: "Home", icon: <SpaceDashboardIcon />, route: "/home" },
  { text: "My Team", icon: <TeamIcon />, route: "/team" },
  {
    text: "My WFH Schedule",
    icon: <WfhScheduleIcon />,
    route: "/wfh-schedule",
  },
  { text: "Create Request", icon: <PostAddIcon />, route: "/create-request" },
];

interface SidebarProps {
  mobileOpen: boolean;
  handleDrawerToggle: () => void;
  container?: Element | (() => Element | null) | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mobileOpen,
  handleDrawerToggle,
  container,
}) => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const location = useLocation(); // Use the useLocation hook to get the current route

  const handleButtonClick = (route: string) => {
    navigate(route);
  };

  const getSidebarItems = () => {
    let basicSideBar = sideBarItems;

    if (
      user?.role === 2 ||
      (user?.role === 1 && user?.position === "Director")
    ) {
      basicSideBar = [
        ...basicSideBar,
        {
          text: "Review Team Requests",
          icon: <InboxIcon />,
          route: "/review-requests",
        },
      ];
    }
    if (user?.role === 1) {
      basicSideBar = [
        ...basicSideBar,
        {
          text: "Department Overview",
          icon: <TeamIcon />,
          route: "/department-overview",
        },
      ];
    }
    return basicSideBar;
  };

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%" }}>
      <Toolbar />
      <List>
        {getSidebarItems().map((item, index) => (
          <ListItem key={index} disablePadding>
            <ListItemButton
              sx={{
                textAlign: "left",
                backgroundColor:
                  location.pathname === item.route ? "navy" : "#f5f5f5",
                color: location.pathname === item.route ? "white" : "inherit",
                "&:hover": {
                  backgroundColor:
                    location.pathname === item.route ? "navy" : "#e0e0e0",
                },
              }}
              data-cy={item.text.toLowerCase().replace(/\s+/g, "-")} // This line adds the data-cy attribute
              onClick={() => handleButtonClick(item.route)}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.route ? "white" : "inherit",
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
    </Box>
  );

  return (
    <>
      <Drawer
        container={container}
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
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
    </>
  );
};

export default Sidebar;
