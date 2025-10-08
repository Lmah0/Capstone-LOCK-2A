"use client";
import { Paper, Typography, Box } from "@mui/material";
import FlightIcon from '@mui/icons-material/Flight';
import { formatUnits } from "../../../utils/unitConversions";

interface FlightModeProps {
    isMetric: boolean;
    followDistance: number;
    flightMode: string;
}

export default function FlightMode({ isMetric, followDistance, flightMode }: FlightModeProps) {
    const distanceToTarget = 19.8;
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
                <FlightIcon sx={{ color: '#3b82f6', fontSize: 30 }} />
                <Typography className="text-white font-bold">
                    {flightMode}
                </Typography>
            </Box>

            {hasTrackedObject ? (
                <Box className="flex flex-col items-end gap-0.5">
                    <Typography variant="caption" className="text-neutral-400 text-xs leading-none">
                        Follow: {formatUnits.distance(followDistance, isMetric)}
                    </Typography>
                    <Box className="flex items-center gap-1">
                        <Typography variant="body2" className="text-neutral-300">
                            Target: {formatUnits.distance(distanceToTarget, isMetric)}
                        </Typography>
                    </Box>
                </Box>
            ) : (
                <Typography variant="body2" className="text-neutral-500">
                    No tracking
                </Typography>
            )}
        </Paper>
    );
}