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
import AssignmentIndIcon from "@mui/icons-material/AssignmentInd";
import BusinessIcon from "@mui/icons-material/Business";

const drawerWidth = 240;

const SidebarNames = {
  HOME: "home",
  TEAM: "team",
  WFH_SCHEDULE: "wfh-schedule",
  CREATE_REQUEST: "create-request",
  REVIEW_REQUESTS: "review-requests",
  DELEGATE: "delegate",
  DEPARTMENT_OVERVIEW: "department-overview",
};

type TSidebarItem = {
  text: string;
  icon: React.ReactNode;
  route: string;
  name: string;
  display?: boolean;
};

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

  const sideBarItems: TSidebarItem[] = [
    {
      text: "Home",
      icon: <SpaceDashboardIcon />,
      route: "/home",
      name: "home",
      display: true,
    },
    {
      text: "My Team",
      icon: <TeamIcon />,
      route: "/team",
      name: "team",
      display: true,
    },
    {
      text: "My WFH Schedule",
      icon: <WfhScheduleIcon />,
      route: "/wfh-schedule",
      name: "wfh-schedule",
      display: true,
    },
    {
      text: "Create Request",
      icon: <PostAddIcon />,
      route: "/create-request",
      name: "create-request",
      display: true,
    },
    {
      text: "Review Team Requests",
      icon: <InboxIcon />,
      route: "/review-requests",
      name: "review-requests",
      display:
        user?.role === 2 || (user?.role === 1 && user?.position === "Director"), // role 2 == manager, and role == 1 HR and directors, but only directors should be able to view
    },
    {
      text: "Delegation",
      icon: <AssignmentIndIcon />,
      route: "/delegate",
      name: "delegate",
      display:
        user?.role === 2 || (user?.role === 1 && user?.position === "Director"), // role 2 == manager, and role == 1 HR and directors, but only directors should be able to view
    },
    {
      text: "Department Overview",
      icon: <BusinessIcon />,
      route: "/department-overview",
      name: "department-overview",
      display: user?.role === 1,
    },
  ];


  const handleButtonClick = (route: string) => {
    navigate(route);
  };

  const [currentTab, setCurrentTab] = useState<string>(SidebarNames.HOME);

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%" }}>
      <Toolbar />
      <List>
        {sideBarItems.map(
          (item, index) =>
            item.display && (
              <ListItem key={index} disablePadding>
                <ListItemButton
                  sx={{
                    textAlign: "left",
                    backgroundColor:
                      currentTab === item.name ? "navy" : "#f5f5f5",
                    color: currentTab === item.name ? "white" : "inherit",
                    "&:hover": {
                      backgroundColor:
                        currentTab === item.name ? "navy" : "#e0e0e0",
                    },
                  }}
                  data-cy={item.text.toLowerCase().replace(/\s+/g, "-")}
                  onClick={() => {
                    handleButtonClick(item.route);
                    setCurrentTab(item.name);
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: currentTab === item.name ? "white" : "inherit",
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            )
        )}
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
