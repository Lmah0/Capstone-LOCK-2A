'use client';
import React, { useState, useEffect } from 'react';
import { Box, Stack, CircularProgress, Typography } from '@mui/material';
import { MapComponent } from './map/MapComponent';
import { ControlPanel } from './ui/ControlPanel';
import Dashboard from './Dashboard';
import MissionStats from './MissionStats';
import { TelemetryPoint, TrajectoryStats } from '@/utils/types';
import { calculateTrajectoryStats } from '@/utils/trajectoryCalculations';
import axios from 'axios';

interface AnalysisViewProps {
  objectId: string;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({ objectId }) => {
  const [telemetryData, setTelemetryData] = useState<TelemetryPoint[]>([]);
  const [trajectoryStats, setTrajectoryStats] = useState<TrajectoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isCompleted, setIsCompleted] = useState(false);
  const [restartTrigger, setRestartTrigger] = useState(0);
  const [skipTrigger, setSkipTrigger] = useState(0);

  useEffect(() => {
    const fetchObjectData = async () => {
      setLoading(true);
      setError(null);    
      try {
       const response = await axios.get(`http://localhost:9875/object/${objectId}`);
       const data = response.data;
           
       const convertedTelemetryData: TelemetryPoint[] = data.telemetryData.map((point: any) => ({
        timestamp: point.timestamp,
        latitude: Number(point.latitude),
        longitude: Number(point.longitude),
        speed: Number(point.speed),
        heading: Number(point.heading)
       }));
                  
        setTelemetryData(convertedTelemetryData);    
        if(convertedTelemetryData.length > 0) {
          const stats = calculateTrajectoryStats(convertedTelemetryData, data.class);
          setTrajectoryStats(stats);
        }   

      } catch (err) {
        console.error('Error fetching object data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };   
    
    fetchObjectData();
  }, [objectId]);

  const handlePauseResume = () => {
    if (isCompleted) {
      handleReplay();
    } else {
      setIsPlaying(!isPlaying);
    }
  };

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

  if (loading) {
    return (
      <Box 
        sx={{ 
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 4
        }}
      >
        <Box
          sx={{
            background: '#ffffff',
            borderRadius: 3,
            p: 5,
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.08)',
            border: '1px solid #e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
            minWidth: 280
          }}
        >
          <CircularProgress
            size={48}
            thickness={3.6}
            sx={{
              color: '#6366f1',
            }}
          />
          
          <Box sx={{ textAlign: 'center' }}>
            <Typography 
              variant="h6" 
              sx={{ 
                color: '#111827',
                fontWeight: 500,
                mb: 0.5
              }}
            >
              Loading Trajectory
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#6b7280',
                fontSize: '14px'
              }}
            >
              Fetching telemetry data...
            </Typography>
          </Box>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box 
        sx={{ 
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 2,
          p: 4,
          textAlign: 'center'
        }}
      >
        <div style={{ color: 'red', fontSize: '18px' }}>Error: {error}</div>
      </Box>
    );
  }

  if (telemetryData.length === 0) {
    return (
      <Box 
        sx={{ 
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <div>No trajectory data available</div>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Dashboard />

      <Box sx={{ flexGrow: 1, p: 3 }}>
        <Stack direction="row" spacing={3} sx={{ height: 'calc(100vh - 140px)' }}>
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
};