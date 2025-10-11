"use client";
import { useEffect } from 'react';
import { Box, Typography, Paper, IconButton, Tooltip } from '@mui/material';
import PushPinIcon from '@mui/icons-material/PushPin';
import { formatUnits } from "../../../utils/unitConversions";
import { telemetryConfig } from "../../../utils/telemetryConfig";
import { useWebSocket } from "@/providers/WebSocketProvider";


interface FlightDataProps {
    pinnedTelemetry: string[];
    setPinnedTelemetry: React.Dispatch<React.SetStateAction<string[]>>;
    isMetric: boolean;
}

export default function FlightData({ pinnedTelemetry, setPinnedTelemetry, isMetric }: FlightDataProps) {
    const { telemetryData, connectionStatus, subscribe } = useWebSocket();
    
    useEffect(() => {
        if(connectionStatus === 'connected') {
            subscribe(['telemetry']);
        }
    }, [connectionStatus]);

    const handlePinToggle = (telemetryKey: string) => {
        if(pinnedTelemetry.includes(telemetryKey)) {
            // Remove from pinned
            setPinnedTelemetry(pinnedTelemetry.filter(item => item !== telemetryKey));
        } else {
            // Add to pinned if we have less than 4 items
            if (pinnedTelemetry.length < 4) {
                setPinnedTelemetry([...pinnedTelemetry, telemetryKey]);
            }
        }
    };

    const DataCard = ({ title, value, unit, icon, color = 'white', telemetryKey, rawValue }: {
        title: string;
        value: number;
        unit: string;
        icon: React.ReactNode;
        color?: string;
        telemetryKey?: string;
        rawValue?: number;
    }) => {
        const isPinned = telemetryKey ? pinnedTelemetry.includes(telemetryKey) : false;
        const canPin = telemetryKey && (isPinned || pinnedTelemetry.length < 4);
        
        // Use universal formatter for all telemetry types
        const formatted = telemetryKey && rawValue !== undefined 
            ? formatUnits.formatTelemetry(rawValue, telemetryKey, isMetric)
            : { value: (value ?? 0).toFixed(2), unit: unit };
        
        return (
            <Paper
                elevation={2}
                sx={{
                    p: 1,
                    backgroundColor: 'rgba(38, 38, 38, 0.9)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 2,
                    height: '100%',
                    position: 'relative',
                }}
            >
                {telemetryKey && (
                    <Tooltip title={isPinned ? "Unpin from HUD" : canPin ? "Pin to HUD" : "Maximum 4 items can be pinned"}>
                        <IconButton
                            onClick={() => handlePinToggle(telemetryKey)}
                            disabled={!canPin}
                            sx={{
                                position: 'absolute',
                                top: 4,
                                right: 4,
                                p: 0.5,
                                color: isPinned ? '#fbbf24' : canPin ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.3)',
                                '&:hover': {
                                    color: isPinned ? '#f59e0b' : canPin ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.3)',
                                },
                                '&.Mui-disabled': {
                                    color: 'rgba(255,255,255,0.3)',
                                },
                            }}
                        >
                            <PushPinIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                    </Tooltip>
                )}
                <Box className="flex items-center mb-1">
                    <Box sx={{ color: color, mr: 0.75, fontSize: 16 }}>
                        {icon}
                    </Box>
                    <Typography className="text-neutral-300 font-medium text-xs">
                        {title}
                    </Typography>
                </Box>
                <Typography variant="subtitle1" className="text-white font-bold mb-0.5">
                    {formatted.value}
                </Typography>
                <Typography variant="caption" className="text-neutral-400 text-xs">
                    {formatted.unit}
                </Typography>
            </Paper>
        );
    };

    return (
        <div className="w-full h-full p-4">
            {!telemetryData ? (
                <Box 
                    sx={{ 
                        display: 'flex', 
                        justifyContent: 'center', 
                        alignItems: 'center', 
                        height: '200px',
                        color: 'rgba(255,255,255,0.7)'
                    }}
                >
                    <Typography variant="h6">Loading telemetry data...</Typography>
                </Box>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {Object.entries(telemetryConfig).map(([key, config]) => {
                        const IconComponent = config.icon;
                        const rawValue = telemetryData?.[key as keyof typeof telemetryData] ?? 0;           
                        return (
                            <DataCard
                                key={key}
                                title={config.label}
                                value={rawValue}
                                unit="" // Unit will be determined by formatTelemetry
                                icon={<IconComponent style={config.iconStyle} />}
                                color={config.color || 'white'}
                                telemetryKey={key}
                                rawValue={rawValue}
                            />
                        );
                    })}
                </div>
            )}
        </div>
    );
}