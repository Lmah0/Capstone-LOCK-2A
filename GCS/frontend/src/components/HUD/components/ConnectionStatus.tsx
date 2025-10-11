"use client";
import { useEffect } from "react";
import ErrorIcon from '@mui/icons-material/Error';
import Tooltip from '@mui/material/Tooltip';
import { useWebSocket } from "@/providers/WebSocketProvider";

export default function ConnectionStatus() {
    const { droneConnection, connectionStatus, subscribe } = useWebSocket();

    useEffect(() => {
        if(connectionStatus === 'connected') {
          subscribe(['connection']);
        }
    }, [connectionStatus]);

    return (
        <div>
            {droneConnection ? (
                <>
                </>
            ) : (
                <Tooltip title="Vehicle connection has been lost">
                    <ErrorIcon color="error" sx={{ fontSize: 42 }} />
                </Tooltip>
            )}
        </div>
    );
}