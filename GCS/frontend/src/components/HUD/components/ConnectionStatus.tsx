"use client";
import ErrorIcon from '@mui/icons-material/Error';
import Tooltip from '@mui/material/Tooltip';
import { useWebSocket } from "@/providers/WebSocketProvider";

export default function ConnectionStatus() {
    const { droneConnection } = useWebSocket();

    return (
        <div>
            {droneConnection ? (
                <></>
            ) : (
                <Tooltip id='vehicle-disconnect-tooltip' title="Vehicle connection has been lost">
                    <ErrorIcon id="drone-disconnected" color="error" sx={{ fontSize: 42 }} />
                </Tooltip>
            )}
        </div>
    );
}