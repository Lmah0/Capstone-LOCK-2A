

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
            {...other}
        >
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
        <div className="w-full h-full">
            <Box sx={{ width: '100%', height: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs 
                        value={value} 
                        onChange={handleChange} 
                        aria-label="info dashboard tabs"
                        sx={{
                            '& .MuiTab-root': {
                                color: 'rgb(163 163 163)',
                                '&.Mui-selected': {
                                    color: 'white',
                                },
                            },
                            '& .MuiTabs-indicator': {
                                backgroundColor: '#3b82f6', // blue-500
                            },
                        }}
                    >
                        <Tab label="Data" {...a11yProps(0)} />
                        <Tab label="Controls" {...a11yProps(1)} />
                        <Tab label="Recorded Objects" {...a11yProps(2)} />
                    </Tabs>
                </Box>
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
        </div>
    );
}