

"use client";
import React, { useState } from 'react';
import { Tabs, Tab, Box } from '@mui/material';
import FlightData from './components/FlightData';
import Controls from './components/Controls';
import RecordedObjects from './components/RecordedObjects';

interface TabPanelProps {
    children?: React.ReactNode;
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
                    bgcolor: 'rgb(23 23 23)', // bg-neutral-900
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

export default function InfoDashBoard() {
    const [value, setValue] = useState(0);

    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
        setValue(newValue);
    };

    return (
        <div className="w-full h-full bg-neutral-900">
            <Box sx={{ 
                width: '100%', 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'rgb(23 23 23)', // bg-neutral-900
            }}>
                <Box sx={{ 
                    borderBottom: 1, 
                    borderColor: 'rgb(64 64 64)', // border-neutral-700
                    bgcolor: 'rgb(38 38 38)', // bg-neutral-800
                    px: 2,
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}>
                    <Tabs 
                        value={value} 
                        onChange={handleChange} 
                        aria-label="info dashboard tabs"
                        sx={{
                            minHeight: 56,
                            '& .MuiTab-root': {
                                color: 'rgb(163 163 163)', // text-neutral-400
                                fontWeight: 500,
                                fontSize: '0.95rem',
                                textTransform: 'none',
                                minHeight: 56,
                                px: 3,
                                transition: 'all 0.2s ease-in-out',
                                '&:hover': {
                                    color: 'rgb(212 212 212)', // text-neutral-300
                                    bgcolor: 'rgba(64, 64, 64, 0.3)', // hover effect
                                },
                                '&.Mui-selected': {
                                    color: 'white',
                                    fontWeight: 600,
                                },
                            },
                            '& .MuiTabs-indicator': {
                                backgroundColor: '#3b82f6', // blue-500
                                height: 3,
                                borderRadius: '2px 2px 0 0',
                            },
                        }}
                    >
                        <Tab label="Flight Data" {...a11yProps(0)} />
                        <Tab label="Controls" {...a11yProps(1)} />
                        <Tab label="Recorded Objects" {...a11yProps(2)} />
                    </Tabs>
                </Box>
                <Box sx={{ 
                    flex: 1, 
                    overflow: 'auto',
                    bgcolor: 'rgb(23 23 23)', // bg-neutral-900
                }}>
                    <TabPanel value={value} index={0}>
                        <FlightData />
                    </TabPanel>
                    <TabPanel value={value} index={1}>
                        <Controls />
                    </TabPanel>
                    <TabPanel value={value} index={2}>
                        <RecordedObjects />
                    </TabPanel>
                </Box>
            </Box>
        </div>
    );
}