import React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import Backdrop from "@mui/material/Backdrop";

export const LoadingSpinner = ({ open }: { open: boolean }) => {
  return (
    <Backdrop open={open} sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <CircularProgress color="primary" />
    </Backdrop>
  );
};
