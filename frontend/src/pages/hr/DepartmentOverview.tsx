import { useNavigate } from "react-router-dom";
import { Container, Box, Typography } from "@mui/material";
import { useContext, useEffect } from "react";
import { UserContext } from "../../context/UserContextProvider";
import { DelegateButton } from "../manager/DelegateButton"; // Ensure this is used if needed
import ErrorOutlineOutlinedIcon from '@mui/icons-material/ErrorOutlineOutlined';
import { RequestHistoryPage } from "./RequestHistory";

export const DepartmentOverviewPage = () => {
    const navigate = useNavigate();
    const { user } = useContext(UserContext);

    useEffect(() => {
        if (!user) {
            navigate("/login");
        }
    }, [user, navigate]);

    return (
        <Container sx={{ flexGrow: 1 }}>
            {/* CHANGE TO BE DEPARTMENT */}
            {(user?.role === 1 || user?.role === 3) && (
                <Box
                    display="flex"
                    alignItems="center"
                    justifyContent="space-between"
                    sx={{
                        my: 4,
                        gap: 2,
                        p: 2,
                        border: "1px solid lightgrey",
                        borderRadius: 1,
                    }}
                >
                    <Box display="flex" alignItems="center" gap={2}>
                        <ErrorOutlineOutlinedIcon />
                        <Typography variant="body2">For WFH/OOO Requests, an approver can be either a reporting manager or a delegated manager</Typography>
                    </Box>
                </Box>
            )}
            <RequestHistoryPage />
        </Container>
    );
};

export default DepartmentOverviewPage;