

"use client";
import { Box, Typography, Paper } from '@mui/material';
import SpeedIcon from '@mui/icons-material/Speed';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import ExploreIcon from '@mui/icons-material/Explore';
import RotateRightIcon from '@mui/icons-material/RotateRight';
import FlightIcon from '@mui/icons-material/Flight';

export default function FlightData() {
    // REPLACE WITH ACTUAL TELEMETRY DATA
    const flightData = {
        speed: 12.5, // m/s
        latitude: 40.7128,
        longitude: -74.0060,
        altitude: 150, // meters
        orientation: 245, // degrees
        bearing: 245, // degrees
        roll: -2.1, // degrees
        pitch: 1.3, // degrees
        yaw: 245.7 // degrees
    };

    const DataCard = ({ title, value, unit, icon, color = 'white' }: {
        title: string;
        value: number;
        unit: string;
        icon: React.ReactNode;
        color?: string;
    }) => (
        <Paper
            elevation={2}
            sx={{
                p: 1,
                backgroundColor: 'rgba(38, 38, 38, 0.9)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 2,
                height: '100%',
            }}
        >
            <Box className="flex items-center mb-1">
                <Box sx={{ color: color, mr: 0.75, fontSize: 16 }}>
                    {icon}
                </Box>
                <Typography className="text-neutral-300 font-medium text-xs">
                    {title}
                </Typography>
            </Box>
            <Typography variant="subtitle1" className="text-white font-bold mb-0.5">
                {value.toFixed(title.includes('Latitude') || title.includes('Longitude') ? 6 : 1)}
            </Typography>
            <Typography variant="caption" className="text-neutral-400 text-xs">
                {unit}
            </Typography>
        </Paper>
    );

    return (
        <div className="w-full h-full p-4">
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {/* Speed */}
                <DataCard
                    title="Ground Speed"
                    value={flightData.speed}
                    unit="m/s"
                    icon={<SpeedIcon />}
                    color="#3b82f6"
                />

                {/* Altitude */}
                <DataCard
                    title="Altitude"
                    value={flightData.altitude}
                    unit="meters"
                    icon={<FlightIcon />}
                    color="#10b981"
                />

                {/* Latitude */}
                <DataCard
                    title="Latitude"
                    value={flightData.latitude}
                    unit="degrees"
                    icon={<LocationOnIcon />}
                    color="#f59e0b"
                />

                {/* Longitude */}
                <DataCard
                    title="Longitude"
                    value={flightData.longitude}
                    unit="degrees"
                    icon={<LocationOnIcon />}
                    color="#f59e0b"
                />

                {/* Orientation/Bearing */}
                <DataCard
                    title="Bearing"
                    value={flightData.bearing}
                    unit="degrees"
                    icon={<ExploreIcon />}
                    color="#8b5cf6"
                />

                {/* Roll */}
                <DataCard
                    title="Roll"
                    value={flightData.roll}
                    unit="degrees"
                    icon={<RotateRightIcon />}
                    color="#ef4444"
                />

                {/* Pitch */}
                <DataCard
                    title="Pitch"
                    value={flightData.pitch}
                    unit="degrees"
                    icon={<RotateRightIcon style={{ transform: 'rotate(90deg)' }} />}
                    color="#06b6d4"
                />

                {/* Yaw */}
                <DataCard
                    title="Yaw"
                    value={flightData.yaw}
                    unit="degrees"
                    icon={<RotateRightIcon style={{ transform: 'rotate(45deg)' }} />}
                    color="#84cc16"
                />
            </div>
        </div>
    );
}