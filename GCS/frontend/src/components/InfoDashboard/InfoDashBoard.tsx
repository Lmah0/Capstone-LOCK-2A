"use client";
import { useState } from 'react';
import { Tabs, Tab, Box } from '@mui/material';
import FlightData from './components/FlightData';
import Controls from './components/Controls';
import RecordedObjects from './components/RecordedObjects';
import { useWebSocket } from '@/providers/WebSocketProvider';

interface TabPanelProps {
    children: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            className="h-full"
            {...other}
        >
            {value === index && (
                <Box sx={{ 
                    p: 3, 
                    height: '100%',
                    bgcolor: 'rgb(23 23 23)',
                    color: 'white',
                }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

function a11yProps(index: number) {
    return {
        id: `simple-tab-${index}`,
        'aria-controls': `simple-tabpanel-${index}`,
    };
}

interface InfoDashBoardProps {
    showHUDElements: boolean;
    setShowHUDElements: React.Dispatch<React.SetStateAction<boolean>>;
    isMetric: boolean;
    setIsMetric: React.Dispatch<React.SetStateAction<boolean>>;
    pinnedTelemetry: string[];
    setPinnedTelemetry: React.Dispatch<React.SetStateAction<string[]>>;
    followDistance: number;
    setFollowDistance: React.Dispatch<React.SetStateAction<number>>;
    flightMode: string;
    setFlightMode: React.Dispatch<React.SetStateAction<string>>;
}

export default function InfoDashBoard({ showHUDElements, setShowHUDElements, isMetric, setIsMetric, pinnedTelemetry, setPinnedTelemetry, followDistance, setFollowDistance, flightMode, setFlightMode }: InfoDashBoardProps) {
    const {droneConnection, isRecording, setIsRecording} = useWebSocket();
    const [value, setValue] = useState(0);

    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
        setValue(newValue);
    };

    return (
        <div id='info-dashboard' className="w-full h-full bg-neutral-900">
            <Box sx={{ 
                width: '100%', 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'rgb(23 23 23)',
            }}>
                <Box sx={{ 
                    borderBottom: 1, 
                    borderColor: droneConnection ? 'rgb(64 64 64)' : 'rgb(239 68 68)',
                    bgcolor: 'rgb(38 38 38)',
                    px: 2,
                    boxShadow: droneConnection 
                        ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' 
                        : '0 4px 6px -1px rgba(239, 68, 68, 0.3), 0 0 0 1px rgba(239, 68, 68, 0.2)'
                }}>
                    <Tabs 
                        id='info-dashboard-tabs'
                        value={value} 
                        onChange={handleChange} 
                        aria-label="info dashboard tabs"
                        sx={{
                            minHeight: 56,
                            '& .MuiTab-root': {
                                color: droneConnection ? 'rgb(163 163 163)' : 'rgb(248 113 113)',
                                fontWeight: 500,
                                fontSize: '0.95rem',
                                textTransform: 'none',
                                minHeight: 56,
                                px: 3,
                                transition: 'all 0.2s ease-in-out',
                                '&:hover': {
                                    color: droneConnection ? 'rgb(212 212 212)' : 'rgb(252 165 165)',
                                    bgcolor: 'rgba(64, 64, 64, 0.3)',
                                },
                                '&.Mui-selected': {
                                    color: droneConnection ? 'white' : 'rgb(239 68 68)',
                                    fontWeight: 600,
                                },
                            },
                            '& .MuiTabs-indicator': {
                                backgroundColor: droneConnection ? '#3b82f6' : '#ef4444',
                                height: 3,
                                borderRadius: '2px 2px 0 0',
                            },
                        }}
                    >
                        <Tab label="Flight Telemetry" {...a11yProps(0)} />
                        <Tab label="Controls" {...a11yProps(1)} />
                        <Tab label="Recorded Objects" {...a11yProps(2)} />
                    </Tabs>
                </Box>
                <Box sx={{ 
                    flex: 1, 
                    overflow: 'auto',
                    bgcolor: 'rgb(23 23 23)',
                }}>
                    <TabPanel value={value} index={0}>
                        <FlightData pinnedTelemetry={pinnedTelemetry} setPinnedTelemetry={setPinnedTelemetry} isMetric={isMetric} />
                    </TabPanel>
                    <TabPanel value={value} index={1}>
                        <Controls 
                            showHUDElements={showHUDElements} 
                            setShowHUDElements={setShowHUDElements} 
                            isRecording={isRecording}
                            setIsRecording={setIsRecording}
                            isMetric={isMetric}
                            setIsMetric={setIsMetric}
                            followDistance={followDistance}
                            setFollowDistance={setFollowDistance}
                            flightMode={flightMode}
                            setFlightMode={setFlightMode}
                        />
                    </TabPanel>
                    <TabPanel value={value} index={2}>
                        <RecordedObjects />
                    </TabPanel>
                </Box>
            </Box>
        </div>
    );
}