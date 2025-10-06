"use client";
import { Paper, Typography, Box } from "@mui/material";
import FlightIcon from '@mui/icons-material/Flight';
import TrackChangesIcon from '@mui/icons-material/TrackChanges';
import { formatUnits } from "../../../utils/unitConversions";

interface FlightModeProps {
    isMetric?: boolean;
}

export default function FlightMode({ isMetric = true }: FlightModeProps) {
    const currentFlightMode = "Loiter";
    const distanceToTarget = 12.6;
    const hasTrackedObject = true;

    return (
        <Paper
            elevation={3}
            sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                p: 2,
                borderRadius: 4,
                backgroundColor: "rgba(0,0,0,0.6)",
                border: "1px solid rgba(255,255,255,0.3)",
                color: "white",
                minWidth: 300,
                minHeight: 70,
            }}
        >
            <Box className="flex items-center gap-1.5">
                <FlightIcon sx={{ color: '#3b82f6', fontSize: 18 }} />
                <Typography variant="subtitle1" className="text-white font-bold">
                    {currentFlightMode}
                </Typography>
            </Box>

            {hasTrackedObject ? (
                <Box className="flex items-center gap-1">
                    <TrackChangesIcon sx={{ color: '#ef4444', fontSize: 16 }} />
                    <Typography variant="body2" className="text-neutral-300">
                        Target: {formatUnits.distance(distanceToTarget, isMetric)}
                    </Typography>
                </Box>
            ) : (
                <Typography variant="body2" className="text-neutral-500">
                    No tracking
                </Typography>
            )}
        </Paper>
    );
}