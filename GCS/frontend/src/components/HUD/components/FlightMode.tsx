

"use client";

import { Box, Paper } from "@mui/material";

export default function FlightMode() {
    return (
        <Paper
            elevation={3}
            sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                p: 2,
                borderRadius: 4,
                backgroundColor: "rgba(0,0,0,0.6)",
                border: "1px solid rgba(255,255,255,0.3)",
                color: "white",
                minWidth: 300,
                minHeight: 90,
            }}
        >
        </Paper>
    );
}