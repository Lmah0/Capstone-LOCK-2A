"use client";
import { Box, Typography, Paper, Chip } from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

interface RecordedObject {
    id: string;
    timestamp: string;
    location: {
        latitude: number;
        longitude: number;
    };
    type: string;
}

export default function RecordedObjects() {
    // Mock recorded objects data - replace with actual data
    const recordedObjects: RecordedObject[] = [
        {
            id: '1',
            timestamp: '2025-01-05 14:32:15',
            location: { latitude: 40.7128, longitude: -74.0060 },
            type: 'Vehicle'
        },
        {
            id: '2',
            timestamp: '2025-01-05 14:31:42',
            location: { latitude: 40.7130, longitude: -74.0058 },
            type: 'Person'
        },
        {
            id: '3',
            timestamp: '2025-01-05 14:27:09',
            location: { latitude: 40.7120, longitude: -74.0070 },
            type: 'Unknown'
        },
        {
            id: '4',
            timestamp: '2025-01-05 14:26:44',
            location: { latitude: 40.7118, longitude: -74.0072 },
            type: 'Vehicle'
        },
        {
            id: '5',
            timestamp: '2025-01-05 14:24:58',
            location: { latitude: 40.7115, longitude: -74.0075 },
            type: 'Unknown'
        }
    ];

    const handleObjectClick = (objectId: string) => {
        // CHANGE TO PROPER URL LATER
        const recordingAnalysisUrl = `http://localhost:3003?objectId=${objectId}`; 
        const newWindow = window.open(recordingAnalysisUrl, `recording-analysis-${objectId}`);  
        if (newWindow) {
            newWindow.focus();
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'Vehicle': return '#3b82f6';
            case 'Person': return '#ef4444';
            case 'Unknown': return '#6b7280';
            default: return '#6b7280';
        }
    };

    return (
        <div className="w-full h-full p-4">    
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto">
                {recordedObjects.map((obj) => (
                    <Paper
                        key={obj.id}
                        elevation={2}
                        onClick={() => handleObjectClick(obj.id)}
                        sx={{
                            p: 1.5,
                            backgroundColor: 'rgba(38, 38, 38, 0.9)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: 2,
                            cursor: 'pointer',
                            transition: 'all 0.2s ease-in-out',
                            height: 'fit-content',
                            '&:hover': {
                                backgroundColor: 'rgba(64, 64, 64, 0.9)',
                                borderColor: 'rgba(255, 255, 255, 0.3)',
                                transform: 'translateY(-1px)',
                            },
                        }}
                    >
                        <Box className="flex items-start justify-between mb-1.5">
                            <Box className="flex-1 min-w-0">
                                <Box className="flex items-center gap-1.5 mb-1">
                                    <Typography variant="subtitle2" className="text-white font-semibold truncate">
                                        {obj.type}
                                    </Typography>
                                    <Chip
                                        label={`#${obj.id}`}
                                        size="small"
                                        sx={{
                                            backgroundColor: getTypeColor(obj.type),
                                            color: 'white',
                                            fontSize: '0.7rem',
                                            height: 18,
                                            minWidth: 'fit-content',
                                        }}
                                    />
                                </Box>
                            </Box>
                            <OpenInNewIcon 
                                sx={{ 
                                    color: 'rgba(255, 255, 255, 0.6)', 
                                    fontSize: 16,
                                    ml: 0.5,
                                    flexShrink: 0
                                }} 
                            />
                        </Box>
                        
                        <Box className="flex flex-col gap-0.5">
                            <Box className="flex items-center gap-1">
                                <AccessTimeIcon sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }} />
                                <Typography variant="caption" className="text-neutral-300 text-xs truncate">
                                    {obj.timestamp}
                                </Typography>
                            </Box>
                            
                            <Box className="flex items-center gap-1">
                                <LocationOnIcon sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: 14 }} />
                                <Typography variant="caption" className="text-neutral-300 text-xs truncate">
                                    {obj.location.latitude.toFixed(4)}, {obj.location.longitude.toFixed(4)}
                                </Typography>
                            </Box>
                        </Box>
                    </Paper>
                ))}
                
                {recordedObjects.length === 0 && (
                    <Paper
                        elevation={1}
                        sx={{
                            p: 4,
                            backgroundColor: 'rgba(38, 38, 38, 0.5)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: 2,
                            textAlign: 'center',
                        }}
                    >
                        <Typography variant="body1" className="text-neutral-400">
                            No recorded objects yet
                        </Typography>
                        <Typography variant="caption" className="text-neutral-500">
                            Start recording to capture detected objects
                        </Typography>
                    </Paper>
                )}
            </div>
        </div>
    );
}