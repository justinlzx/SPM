// src/common/Sidebar.tsx
import * as React from "react";
import { useContext, useEffect, useState } from "react";
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
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';

import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

const drawerWidth = 240;

const defaultSideBarItems = [
  { text: "Home", icon: <SpaceDashboardIcon />, route: "/home" },
  { text: "My Team", icon: <TeamIcon />, route: "/team" },
  { text: "My WFH Schedule", icon: <WfhScheduleIcon />, route: "/wfh-schedule" },
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

  interface SidebarItem {
    text: string;
    icon: React.ReactNode;
    route: string;
  }

  type SidebarItems = SidebarItem[];

  const [basicSideBar, setBasicSideBar] = useState<SidebarItems>(defaultSideBarItems);

  useEffect(() => {
    const fetchSubordinateData = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/arrangements/subordinates/${user?.id}`);

        if (user?.role === 2 || (user?.role === 1 && user?.position === "Director")) {
          setBasicSideBar((prevSidebar: SidebarItem[]) => [
            ...prevSidebar,
            { text: "Review Team Requests", icon: <InboxIcon />, route: "/review-requests" },
            { text: "Delegation", icon: <AssignmentIndIcon />, route: "/delegate" },
          ]);
        }
      } catch (error) {
        const err = error as { response?: { data: string } };
        if (err.response?.data !== "manager ID not found") {
        }
      }
    };

    fetchSubordinateData();
  }, [user]);

  const handleButtonClick = (route: string) => {
    navigate(route);
  };

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%" }}>
      <Toolbar />
      <List>
        {basicSideBar.map((item: SidebarItem, index: number) => (
          <ListItem key={index} disablePadding>
            <ListItemButton
              sx={{
                textAlign: "left",
                backgroundColor: location.pathname === item.route ? "navy" : "#f5f5f5",
                color: location.pathname === item.route ? "white" : "inherit",
                "&:hover": {
                  backgroundColor: location.pathname === item.route ? "navy" : "#e0e0e0",
                },
              }}
              data-cy={item.text.toLowerCase().replace(/\s+/g, "-")}
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
    <Drawer
      variant="permanent" // Set Drawer to permanent variant only
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          bgcolor: "#f5f5f5",
        },
      }}
      open
      container={container}
    >
      {drawer}
    </Drawer>
  );
};

export default Sidebar;
