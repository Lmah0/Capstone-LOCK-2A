"use client";
import ErrorIcon from '@mui/icons-material/Error';
import Tooltip from '@mui/material/Tooltip';

export default function ConnectionStatus() {

    return (
        <div>
            <Tooltip title="Vehicle connection has been lost">
                <ErrorIcon color="error" sx={{ fontSize: 42 }} />
            </Tooltip>
        </div>
    );
}