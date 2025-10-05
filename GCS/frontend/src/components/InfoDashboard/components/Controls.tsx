"use client";
import { Switch, FormControlLabel, Box, Typography, Paper, Radio, RadioGroup } from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import PublicIcon from '@mui/icons-material/Public';

interface ControlsProps {
    showHUDElements: boolean;
    setShowHUDElements: React.Dispatch<React.SetStateAction<boolean>>;
    isRecording: boolean;
    setIsRecording: React.Dispatch<React.SetStateAction<boolean>>;
    isMetric: boolean;
    setIsMetric: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function Controls({ showHUDElements, setShowHUDElements, isRecording, setIsRecording, isMetric, setIsMetric }: ControlsProps) {

    const handleHudToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setShowHUDElements(event.target.checked);
    };

    const handleRecordingToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsRecording(event.target.checked);
    };

    const handleMetricToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsMetric(event.target.value === 'metric');
    };

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
            </div>
        </div>
    );
}