"use client";
import ErrorIcon from '@mui/icons-material/Error';
import Tooltip from '@mui/material/Tooltip';
import { useWebSocket } from "@/providers/WebSocketProvider";

export default function ConnectionStatus() {
    const { droneConnection } = useWebSocket();

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