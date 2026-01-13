"use client";
import React from 'react';
import { Box, Chip } from '@mui/material';
import { WifiOff, Wifi, WifiTethering } from '@mui/icons-material';
import { useWebSocket } from '@/providers/WebSocketProvider';

export default function ServerConnection() {
  const { connectionStatus } = useWebSocket();

  const getStatusConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: '#4ade80',
          bgColor: '#16a34a20',
          icon: <Wifi sx={{ fontSize: 16 }} />,
          text: 'Connected'
        };
      case 'connecting':
        return {
          color: '#f59e0b',
          bgColor: '#f59e0b20',
          icon: <WifiTethering sx={{ fontSize: 16 }} />,
          text: 'Connecting'
        };
      default:
        return {
          color: '#6b7280',
          bgColor: '#6b728020',
          icon: <WifiOff sx={{ fontSize: 16 }} />,
          text: 'Disconnected'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Box className="flex items-center gap-2">
      <Chip
        icon={config.icon}
        label={config.text}
        size="small"
        sx={{
          backgroundColor: config.bgColor,
          color: config.color,
          border: `1px solid ${config.color}40`,
          fontWeight: 600,
          fontSize: '0.75rem',
          '& .MuiChip-icon': {
            color: config.color,
          }
        }}
      />
    </Box>
  );
};
