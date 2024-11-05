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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const drawerWidth = 240;

interface SidebarItem {
  text: string;
  icon: React.ReactNode;
  route: string;
}

const defaultSideBarItems: SidebarItem[] = [
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
  const location = useLocation();
  const [basicSideBar, setBasicSideBar] = useState<SidebarItem[]>(defaultSideBarItems);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubordinateData = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      let updatedSidebar = [...defaultSideBarItems];

      try {
        // First check if user is manager or director
        if (user?.role === 2 || (user?.role === 1 && user?.position === "Director")) {
          const subordinatesResponse = await axios.get(
            `${BACKEND_URL}/arrangements/subordinates/${user.id}`
          );

          if (subordinatesResponse.data) {
            updatedSidebar.push(
              { text: "Review Team Requests", icon: <InboxIcon />, route: "/review-requests" },
              { text: "Delegation", icon: <AssignmentIndIcon />, route: "/delegate" },
            );
          }
        }

        // Fetch employee department data
        const employeeResponse = await axios.get(`${BACKEND_URL}/employees/${user.id}`);

        if (employeeResponse.data && employeeResponse.data.dept === "HR") {
          // Check if "Department Overview" already exists
          const departmentOverviewExists = updatedSidebar.some(item => item.text === "Department Overview");

          // To avoid Multiple instances of department overview
          if (!departmentOverviewExists) {
            updatedSidebar.push({
              text: "Department Overview",
              icon: <SpaceDashboardIcon />,
              route: "/department-overview"
            });
          }
        }

        // Update the sidebar state only once
        setBasicSideBar(updatedSidebar);

      } catch (error) {
        console.error("Error fetching data:", error);
        const err = error as { response?: { data?: string; status?: number } };

        if (err.response?.status === 404) {
          setError("Employee data not found");
        } else if (err.response?.data !== "manager ID not found") {
          setError("Error loading sidebar data");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubordinateData();
  }, [user]);

  const handleButtonClick = (route: string) => {
    navigate(route);
  };

  if (isLoading) {
    return <Box sx={{ p: 2 }}>Loading...</Box>;
  }

  if (error) {
    console.error("Sidebar Error:", error);
  }

  const drawer = (
    <Box sx={{ bgcolor: "#f5f5f5", height: "100%" }}>
      <Toolbar />
      <List>
        {basicSideBar.map((item, index) => (
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