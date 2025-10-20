'use client';
import React, { useState, useEffect } from 'react';
import { Box, Stack } from '@mui/material';
import { MapComponent } from '../components/map/MapComponent'
import { ControlPanel } from '../components/ui/ControlPanel';
import Dashboard from '../components/Dashboard';
import MissionStats from '../components/MissionStats';
import { EXAMPLE_TELEMETRY_DATA } from '@/data/exampleTelemetry';
import { calculateTrajectoryStats } from '@/utils/trajectoryCalculations';
import { TelemetryPoint, TrajectoryStats } from '@/utils/types';

export default function HomePage() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [isCompleted, setIsCompleted] = useState(false);
  const [restartTrigger, setRestartTrigger] = useState(0);
  const [skipTrigger, setSkipTrigger] = useState(0);
  const [telemetryData, setTelemetryData] = useState<TelemetryPoint[]>(EXAMPLE_TELEMETRY_DATA);
  const [trajectoryStats, setTrajectoryStats] = useState<TrajectoryStats | null>(null);

  useEffect(() => {
    if (telemetryData.length > 0) {
      const stats = calculateTrajectoryStats(telemetryData);
      setTrajectoryStats(stats);
    }
  }, [telemetryData]);

  const handlePauseResume = () => {
    if (isCompleted) {
      // If completed, restart the animation
      handleReplay();
    } else {
      // Normal pause/resume logic
      setIsPlaying(!isPlaying);
    }
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const objectId = urlParams.get('objectId');

    if(objectId) {
      console.log('Loading data for object:', objectId);
      // QUERY DATA BASED ON OBJECT ID FROM DATABASE
      // SET TO telemetryData (setTelemetryData)
    }
  }, []);

  const handleReplay = () => {
    setIsPlaying(true);
    setIsCompleted(false);
    setRestartTrigger(prev => prev + 1);
  };

  const handleSkip = () => {
    setSkipTrigger(prev => prev + 1);
  };

  const handleAnimationEnd = () => {
    setIsPlaying(false);
    setIsCompleted(true);
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header */}
      <Dashboard />

      <Box sx={{ flexGrow: 1, p: 3 }}>
        <Stack direction="row" spacing={3} sx={{ height: 'calc(100vh - 140px)' }}>
          {/* Left Panel - Controls and Stats */}
          <Box sx={{ width: 300 }}>
            <Stack spacing={3} sx={{ height: '100%' }}>
              <ControlPanel 
                isPlaying={isPlaying}
                isCompleted={isCompleted}
                onPauseResume={handlePauseResume}
                onReplay={handleReplay}
                onSkip={handleSkip}
              />
              <Box sx={{ flexGrow: 1, minHeight: 0 }}>
                <MissionStats trajectoryStats={trajectoryStats} />
              </Box>
            </Stack>
          </Box>

          {/* Main Map Area */}
          <Box 
            sx={{ 
              flexGrow: 1,
              borderRadius: 3,
              overflow: 'hidden',
              boxShadow: '0 12px 40px rgba(0,0,0,0.12)',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              transition: 'all 0.3s ease',
              '&:hover': {
                boxShadow: '0 20px 50px rgba(0,0,0,0.15)'
              }
            }}
          >
            <MapComponent 
              telemetryData={telemetryData}
              isPlaying={isPlaying}
              restartTrigger={restartTrigger}
              skipTrigger={skipTrigger}
              onAnimationEnd={handleAnimationEnd}
            />
          </Box>
        </Stack>
      </Box>
    </Box>
  );
}