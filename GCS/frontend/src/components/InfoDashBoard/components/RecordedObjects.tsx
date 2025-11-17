"use client";
import { useEffect } from 'react';
import { Box, Typography, Paper, IconButton, Button, Avatar } from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import DeleteIcon from '@mui/icons-material/Delete';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import PersonIcon from '@mui/icons-material/Person';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { useState } from 'react';
import axios from 'axios';

interface RecordedObject {
    objectID: string;
    classification: string;
    timestamp: string;
}

export default function RecordedObjects() {
    const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
    const [recordedObjects, setRecordedObjects] = useState<RecordedObject[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRecordedObjects = async () => {
            try {
                const response = await axios.get<RecordedObject[]>('http://localhost:8766/objects');
                setRecordedObjects(response.data);
            } catch (error) {
                console.error('Error fetching recorded objects:', error);
                setRecordedObjects([]);
            } finally {
                setLoading(false);
            }
        };

        fetchRecordedObjects();
    }, []);

    const handleObjectClick = (objectId: string) => {
        if(deleteConfirmId === objectId) return; 

        const recordingAnalysisUrl = `http://localhost:9876?objectId=${objectId}`; 
        const newWindow = window.open(recordingAnalysisUrl, `recording-analysis-${objectId}`);  
        if (newWindow) {
            newWindow.focus();
        }
    };

    const handleDeleteClick = (objectId: string, event: React.MouseEvent) => {
        event.stopPropagation();
        setDeleteConfirmId(objectId);
    };

    const handleConfirmDelete = async (objectId: string, event: React.MouseEvent) => {
        event.stopPropagation();    
        try {
            const resp = await axios.delete(`http://localhost:8766/delete/object/${objectId}`);
            if(resp.status === 200) {
                setRecordedObjects(prev => prev.filter(obj => obj.objectID !== objectId));
            }
        } catch (error) {
            alert('Failed to delete object.');
        } finally {
            setDeleteConfirmId(null);
        }
    };

    const handleCancelDelete = (event: React.MouseEvent) => {
        event.stopPropagation();
        setDeleteConfirmId(null);
    };

    const formatTimestamp = (timestamp: string | null) => {
        if (!timestamp) return 'Unknown time';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch (error) {
            return 'Invalid date';
        }
    };

    const getObjectConfig = (classification: string) => {
        switch (classification.toLowerCase()) {
            case 'vehicle':
                return {
                    icon: <DirectionsCarIcon sx={{ fontSize: 24 }} />,
                    color: '#3b82f6',
                    bgColor: 'rgba(59, 130, 246, 0.1)',
                    label: 'Vehicle',
                };
            case 'person':
                return {
                    icon: <PersonIcon sx={{ fontSize: 24 }} />,
                    color: '#ef4444',
                    bgColor: 'rgba(239, 68, 68, 0.1)',
                    label: 'Person',
                };
            default:
                return {
                    icon: <HelpOutlineIcon sx={{ fontSize: 24 }} />,
                    color: '#6b7280',
                    bgColor: 'rgba(107, 114, 128, 0.1)',
                    label: "Unknown",
                };
        }
    };

    if (loading) {
        return (
            <div className="w-full h-full p-6 flex items-center justify-center">
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 2,
                        p: 4,
                        borderRadius: 3,
                        background: 'rgba(255, 255, 255, 0.05)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                >
                    <Box
                        sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            border: '3px solid rgba(59, 130, 246, 0.3)',
                            borderTop: '3px solid #3b82f6',
                            animation: 'spin 1s linear infinite',
                            '@keyframes spin': {
                                '0%': { transform: 'rotate(0deg)' },
                                '100%': { transform: 'rotate(360deg)' },
                            },
                        }}
                    />
                    <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                        Loading recorded objects...
                    </Typography>
                </Box>
            </div>
        );
    }

    return (
        <div className="w-full h-full p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 overflow-y-auto">
                {recordedObjects.map((obj) => {
                    const config = getObjectConfig(obj.classification);
                    
                    return (
                        <Paper
                            key={obj.objectID}
                            elevation={3}
                            onClick={() => handleObjectClick(obj.objectID)}
                            sx={{
                                position: 'relative',
                                borderRadius: 3,
                                overflow: 'hidden',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease-in-out',
                                background: deleteConfirmId === obj.objectID 
                                    ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%)'
                                    : 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
                                backdropFilter: 'blur(10px)',
                                border: deleteConfirmId === obj.objectID 
                                    ? '1px solid rgba(239, 68, 68, 0.3)'
                                    : '1px solid rgba(255, 255, 255, 0.1)',
                                height: 140,
                                '&:hover': {
                                    transform: 'translateY(-2px)',
                                    boxShadow: deleteConfirmId === obj.objectID
                                        ? '0 8px 25px rgba(239, 68, 68, 0.15)'
                                        : '0 8px 25px rgba(0, 0, 0, 0.1)',
                                    background: deleteConfirmId === obj.objectID
                                        ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%)'
                                        : 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.08) 100%)',
                                    borderColor: deleteConfirmId === obj.objectID
                                        ? 'rgba(239, 68, 68, 0.4)'
                                        : 'rgba(255, 255, 255, 0.2)',
                                },
                            }}
                        >
                            {deleteConfirmId === obj.objectID ? (
                                <Box 
                                    sx={{
                                        height: '100%',
                                        width: '100%',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: 2,
                                        p: 2,
                                    }}
                                >
                                    <Box sx={{ textAlign: 'center' }}>
                                        <Typography variant="h6" sx={{ color: '#ef4444', fontWeight: 600, mb: 0.5 }}>
                                            Delete Object?
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                                            This action cannot be undone
                                        </Typography>
                                    </Box>
                                    
                                    <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            onClick={handleCancelDelete}
                                            sx={{
                                                flex: 1,
                                                color: 'white',
                                                borderColor: 'rgba(255, 255, 255, 0.3)',
                                                fontSize: '0.75rem',
                                                py: 0.5,
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                        <Button
                                            variant="contained"
                                            size="small"
                                            onClick={(e) => handleConfirmDelete(obj.objectID, e)}
                                            sx={{
                                                flex: 1,
                                                backgroundColor: '#ef4444',
                                                fontSize: '0.75rem',
                                                py: 0.5,
                                            }}
                                        >
                                            Delete
                                        </Button>
                                    </Box>
                                </Box>
                            ) : (
                                <>
                                    <Box
                                        sx={{
                                            position: 'absolute',
                                            top: 0,
                                            left: 0,
                                            right: 0,
                                            height: '50%',
                                            background: `linear-gradient(180deg, ${config.color}15 0%, transparent 100%)`,
                                            zIndex: 0,
                                        }}
                                    />

                                    {/* Open in new tab icon*/}
                                    <IconButton
                                        size="small"
                                        sx={{
                                            position: 'absolute',
                                            top: 8,
                                            right: 8,
                                            zIndex: 10,
                                            color: 'rgba(255, 255, 255, 0.6)',
                                            backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                            backdropFilter: 'blur(10px)',
                                        }}
                                    >
                                        <OpenInNewIcon sx={{ fontSize: 18 }} />
                                    </IconButton>

                                    {/* Delete button */}
                                    <IconButton
                                        onClick={(e) => handleDeleteClick(obj.objectID, e)}
                                        sx={{
                                            position: 'absolute',
                                            bottom: 8,
                                            right: 8,
                                            zIndex: 10,
                                            color: '#ef4444',
                                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                            border: '1px solid rgba(239, 68, 68, 0.3)',
                                            width: 32,
                                            height: 32,
                                            '&:hover': {
                                                backgroundColor: 'rgba(255, 255, 255, 1)',
                                            },
                                        }}
                                    >
                                        <DeleteIcon sx={{ fontSize: 18 }} />
                                    </IconButton>

                                    {/* Content */}
                                    <Box sx={{ position: 'relative', zIndex: 1, p: 2.5, height: '100%' }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', mb: 2 }}>
                                            <Avatar
                                                sx={{
                                                    backgroundColor: config.color,
                                                    color: 'white',
                                                    width: 45,
                                                    height: 45,
                                                    boxShadow: `0 4px 12px ${config.color}30`,
                                                }}
                                            >
                                                {config.icon}
                                            </Avatar>
                                        </Box>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography 
                                                variant="h6" 
                                                sx={{ 
                                                    color: 'white', 
                                                    fontWeight: 600, 
                                                    mb: 0.5,
                                                    fontSize: '1.1rem'
                                                }}
                                            >
                                                {config.label}
                                            </Typography>
                                        </Box>
                                        <Box sx={{ position: 'absolute', bottom: 12, left: 16 }}>
                                            <Typography 
                                                variant="caption" 
                                                sx={{ 
                                                    color: 'rgba(255, 255, 255, 0.6)',
                                                    fontSize: '0.7rem',
                                                    fontWeight: 500
                                                }}
                                            >
                                                {formatTimestamp(obj.timestamp)}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </>
                            )}
                        </Paper>
                    );
                })}
                
                {recordedObjects.length === 0 && !loading && (
                    <Box
                        sx={{
                            gridColumn: '1 / -1',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            p: 6,
                            borderRadius: 3,
                            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            minHeight: 200,
                        }}
                    >
                        <Avatar
                            sx={{
                                backgroundColor: 'rgba(107, 114, 128, 0.2)',
                                color: 'rgba(255, 255, 255, 0.5)',
                                width: 60,
                                height: 60,
                                mb: 2,
                            }}
                        >
                            <HelpOutlineIcon sx={{ fontSize: 30 }} />
                        </Avatar>
                        <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)', mb: 1, fontWeight: 500 }}>
                            No Recorded Objects
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)', textAlign: 'center' }}>
                            Start recording to capture and track detected objects
                        </Typography>
                    </Box>
                )}
            </div>
        </div>
    );
}