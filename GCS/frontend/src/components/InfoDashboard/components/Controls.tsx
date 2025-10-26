"use client";
import { Switch, FormControlLabel, Box, Typography, Paper, Radio, RadioGroup, TextField, InputAdornment, Select, MenuItem, FormControl } from '@mui/material';
import { useState, useEffect } from 'react';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import PublicIcon from '@mui/icons-material/Public';
import StraightenIcon from '@mui/icons-material/Straighten';
import FlightIcon from '@mui/icons-material/Flight';
import { convertDistance } from '../../../utils/unitConversions';

interface ControlsProps {
    showHUDElements: boolean;
    setShowHUDElements: React.Dispatch<React.SetStateAction<boolean>>;
    isRecording: boolean;
    setIsRecording: React.Dispatch<React.SetStateAction<boolean>>;
    isMetric: boolean;
    setIsMetric: React.Dispatch<React.SetStateAction<boolean>>;
    followDistance: number;
    setFollowDistance: React.Dispatch<React.SetStateAction<number>>;
    flightMode: string;
    setFlightMode: React.Dispatch<React.SetStateAction<string>>;
}

export default function Controls({ showHUDElements, setShowHUDElements, isRecording, setIsRecording, isMetric, setIsMetric, followDistance, setFollowDistance, flightMode, setFlightMode }: ControlsProps) {
    const [inputValue, setInputValue] = useState('');

    useEffect(() => {
        const displayDistance = isMetric ? followDistance : convertDistance.metersToFeet(followDistance);
        setInputValue(displayDistance.toString());
    }, [followDistance, isMetric]);

    const handleHudToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setShowHUDElements(event.target.checked);
    };
    const handleRecordingToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsRecording(event.target.checked);
    };
    const handleMetricToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsMetric(event.target.value === 'metric');
    };

    const handleFollowDistanceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.value;
        setInputValue(newValue);
        
        const value = parseFloat(newValue);
        if (!isNaN(value) && value > 0) {
            setFollowDistance(isMetric ? value : value / convertDistance.metersToFeet(1));
        }
    };

    const handleFlightModeChange = (event: any) => {
        setFlightMode(event.target.value);
    };

    const flightModes = [
        'Loiter',
        'Manual',
        'Fly By Wire A',
        'Fly By Wire B',
        'Auto',
        'Guided'
    ];

    return (
        <div className="w-full h-full p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {/* HUD Elements Control */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 2,
                        backgroundColor: 'rgba(38, 38, 38, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                    }}
                >
                    <Box className="flex items-center mb-2">
                        {showHUDElements ? (
                            <VisibilityIcon sx={{ color: 'white', mr: 1.5, fontSize: 20 }} />
                        ) : (
                            <VisibilityOffIcon sx={{ color: 'white', mr: 1.5, fontSize: 20 }} />
                        )}
                        <Typography variant="subtitle1" className="text-white font-semibold">
                            HUD Elements
                        </Typography>
                    </Box>
                    
                    <Typography variant="caption" className="text-neutral-300 mb-3 block">
                        Toggle HUD overlay visibility
                    </Typography>
                    
                    <FormControlLabel
                        control={
                            <Switch
                                checked={showHUDElements}
                                onChange={handleHudToggle}
                                size="small"
                                sx={{
                                    '& .MuiSwitch-switchBase.Mui-checked': {
                                        color: '#3b82f6',
                                    },
                                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                        backgroundColor: '#3b82f6',
                                    },
                                    '& .MuiSwitch-track': {
                                        backgroundColor: '#6b7280',
                                    },
                                }}
                            />
                        }
                        label={
                            <Typography variant="body2" className="text-white">
                                {showHUDElements ? 'Visible' : 'Hidden'}
                            </Typography>
                        }
                    />
                </Paper>

                {/* Recording Control */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 2,
                        backgroundColor: 'rgba(38, 38, 38, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                    }}
                >
                    <Box className="flex items-center mb-2">
                        <RadioButtonCheckedIcon sx={{ color: isRecording ? '#ef4444' : 'white', mr: 1.5, fontSize: 20 }} />
                        <Typography variant="subtitle1" className="text-white font-semibold">
                            Record Objects
                        </Typography>
                    </Box>
                    
                    <Typography variant="caption" className="text-neutral-300 mb-3 block">
                        Record tracked objects
                    </Typography>
                    
                    <FormControlLabel
                        control={
                            <Switch
                                checked={isRecording}
                                onChange={handleRecordingToggle}
                                size="small"
                                sx={{
                                    '& .MuiSwitch-switchBase.Mui-checked': {
                                        color: '#ef4444',
                                    },
                                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                        backgroundColor: '#ef4444',
                                    },
                                    '& .MuiSwitch-track': {
                                        backgroundColor: '#6b7280',
                                    },
                                }}
                            />
                        }
                        label={
                            <Typography variant="body2" className="text-white">
                                {isRecording ? 'Recording' : 'Stopped'}
                            </Typography>
                        }
                    />
                </Paper>

                {/* Units Control */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 2,
                        backgroundColor: 'rgba(38, 38, 38, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                    }}
                >
                    <Box className="flex items-center mb-2">
                        <PublicIcon sx={{ color: 'white', mr: 1.5, fontSize: 20 }} />
                        <Typography variant="subtitle1" className="text-white font-semibold">
                            Units
                        </Typography>
                    </Box>
                    
                    <Typography variant="caption" className="text-neutral-300 mb-3 block">
                        Display units system
                    </Typography>
                    
                    <RadioGroup
                        value={isMetric ? 'metric' : 'imperial'}
                        onChange={handleMetricToggle}
                        row
                    >
                        <FormControlLabel
                            value="metric"
                            control={
                                <Radio
                                    size="small"
                                    sx={{
                                        color: '#6b7280',
                                        '&.Mui-checked': {
                                            color: '#10b981',
                                        },
                                    }}
                                />
                            }
                            label={
                                <Typography variant="body2" className="text-white">
                                    Metric
                                </Typography>
                            }
                        />
                        <FormControlLabel
                            value="imperial"
                            control={
                                <Radio
                                    size="small"
                                    sx={{
                                        color: '#6b7280',
                                        '&.Mui-checked': {
                                            color: '#10b981',
                                        },
                                    }}
                                />
                            }
                            label={
                                <Typography variant="body2" className="text-white">
                                    Imperial
                                </Typography>
                            }
                        />
                    </RadioGroup>
                </Paper>

                {/* Follow Distance Control */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 2,
                        backgroundColor: 'rgba(38, 38, 38, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                    }}
                >
                    <Box className="flex items-center mb-2">
                        <StraightenIcon sx={{ color: 'white', mr: 1.5, fontSize: 20 }} />
                        <Typography variant="subtitle1" className="text-white font-semibold">
                            Follow Distance
                        </Typography>
                    </Box>
                    
                    <Typography variant="caption" className="text-neutral-300 mb-3 block">
                        Minimum distance to maintain from target
                    </Typography>
                    
                    <TextField
                        type="number"
                        value={inputValue}
                        onChange={handleFollowDistanceChange}
                        size="small"
                        InputProps={{
                            endAdornment: (
                                <InputAdornment position="end">
                                    <Typography variant="body2" sx={{ color: '#9ca3af' }}>
                                        {isMetric ? 'meters' : 'feet'}
                                    </Typography>
                                </InputAdornment>
                            ),
                            inputProps: {
                                min: 0.1,
                                step: 1,
                            },
                        }}
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                                '& fieldset': {
                                    borderColor: 'rgba(156, 163, 175, 0.3)',
                                },
                                '&:hover fieldset': {
                                    borderColor: 'rgba(156, 163, 175, 0.5)',
                                },
                                '&.Mui-focused fieldset': {
                                    borderColor: '#10b981',
                                },
                                '& input': {
                                    color: 'white',
                                },
                            },
                        }}
                        fullWidth
                    />
                </Paper>

                {/* Flight Mode Control */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 2,
                        backgroundColor: 'rgba(38, 38, 38, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                    }}
                >
                    <Box className="flex items-center mb-2">
                        <FlightIcon sx={{ color: 'white', mr: 1.5, fontSize: 20 }} />
                        <Typography variant="subtitle1" className="text-white font-semibold">
                            Flight Mode
                        </Typography>
                    </Box>
                    
                    <Typography variant="caption" className="text-neutral-300 mb-3 block">
                        Select aircraft flight mode
                    </Typography>
                    
                    <FormControl fullWidth size="small">
                        <Select
                            value={flightMode}
                            onChange={handleFlightModeChange}
                            sx={{
                                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                                color: 'white',
                                '& .MuiOutlinedInput-notchedOutline': {
                                    borderColor: 'rgba(156, 163, 175, 0.3)',
                                },
                                '&:hover .MuiOutlinedInput-notchedOutline': {
                                    borderColor: 'rgba(156, 163, 175, 0.5)',
                                },
                                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                                    borderColor: '#10b981',
                                },
                                '& .MuiSelect-icon': {
                                    color: 'white',
                                },
                            }}
                            MenuProps={{
                                PaperProps: {
                                    sx: {
                                        backgroundColor: 'rgba(38, 38, 38, 0.95)',
                                        border: '1px solid rgba(255, 255, 255, 0.2)',
                                        '& .MuiMenuItem-root': {
                                            color: 'white',
                                            '&:hover': {
                                                backgroundColor: 'rgba(55, 65, 81, 0.8)',
                                            },
                                            '&.Mui-selected': {
                                                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                                                '&:hover': {
                                                    backgroundColor: 'rgba(16, 185, 129, 0.3)',
                                                },
                                            },
                                        },
                                    },
                                },
                            }}
                        >
                            {flightModes.map((mode) => (
                                <MenuItem key={mode} value={mode}>
                                    {mode}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Paper>
            </div>
        </div>
    );
}