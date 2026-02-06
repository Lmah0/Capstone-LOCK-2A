"use client";
import React from 'react';
import { Card, CardContent, Typography, Box, Stack } from '@mui/material';
import { Speed, TrendingUp, AccessTime, Straighten, Category } from '@mui/icons-material';
import { formatMissionDuration, formatSpeed, formatDistance } from '@/utils/trajectoryCalculations';
import { TrajectoryStats } from '@/utils/types';

interface MissionStatsProps {
  trajectoryStats: TrajectoryStats | null;
}

export default function MissionStats({ trajectoryStats }: MissionStatsProps) {
  if (!trajectoryStats) {
    return (
      <Card 
        sx={{ 
          background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
          border: '1px solid rgba(0,0,0,0.05)',
          borderRadius: 3,
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ color: '#667eea', fontWeight: 600 }}>
            Loading statistics...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const stats = [
    {
      icon: <Category sx={{ fontSize: 20, color: '#8b5cf6' }} />,
      label: 'Object Class',
      value: trajectoryStats.objectClass || 'Unknown',
      color: '#8b5cf6'
    },
    {
      icon: <AccessTime sx={{ fontSize: 20, color: '#667eea' }} />,
      label: 'Mission Duration',
      value: formatMissionDuration(trajectoryStats.missionDuration),
      color: '#667eea'
    },
    {
      icon: <Speed sx={{ fontSize: 20, color: '#1976d2' }} />,
      label: 'Average Speed',
      value: formatSpeed(trajectoryStats.averageSpeed),
      color: '#1976d2'
    },
    {
      icon: <TrendingUp sx={{ fontSize: 20, color: '#2e7d32' }} />,
      label: 'Max Speed',
      value: formatSpeed(trajectoryStats.maxSpeed),
      color: '#2e7d32'
    },
    {
      icon: <Straighten sx={{ fontSize: 20, color: '#f57c00' }} />,
      label: 'Total Distance',
      value: formatDistance(trajectoryStats.totalDistance),
      color: '#f57c00'
    }
  ];

  return (
    <Card 
      sx={{ 
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: 3,
        boxShadow: '0 8px 25px rgba(0,0,0,0.08)',
        height: '100%',
        maxHeight: 'calc(100vh - 280px)',
        overflow: 'hidden',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 12px 35px rgba(0,0,0,0.12)',
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent id='mission-stats' sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 700,
            color: '#1e293b',
            mb: 2,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}
        >
          <Box 
            sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              animation: 'pulse 2s infinite'
            }} 
          />
          Mission Statistics
        </Typography>
        
        <Box sx={{ 
          flexGrow: 1, 
          overflowY: 'auto',
          pr: 1,
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f5f9',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            borderRadius: '3px',
            '&:hover': {
              background: 'linear-gradient(135deg, #2563eb 0%, #1e40af 100%)',
            }
          },
        }}>
          <Stack spacing={2}>
            {stats.map((stat, index) => (
              <Box 
                key={index}
                className="fade-in"
                sx={{ 
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                  border: `1px solid ${stat.color}20`,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: `linear-gradient(135deg, ${stat.color}05 0%, ${stat.color}02 100%)`,
                    transform: 'translateX(4px)',
                    boxShadow: `0 4px 15px ${stat.color}20`,
                    borderColor: `${stat.color}40`
                  },
                  animationDelay: `${index * 0.1}s`
                }}
              >
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Box
                    sx={{
                      p: 1.2,
                      borderRadius: 2,
                      background: `linear-gradient(135deg, ${stat.color}15 0%, ${stat.color}25 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      minWidth: 40,
                      minHeight: 40,
                      boxShadow: `0 4px 10px ${stat.color}20`
                    }}
                  >
                    {React.cloneElement(stat.icon, { 
                      sx: { 
                        fontSize: 20, 
                        color: stat.color,
                        filter: 'brightness(1.1)'
                      } 
                    })}
                  </Box>
                  <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#64748b',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.8,
                        fontSize: '0.7rem',
                        display: 'block',
                        lineHeight: 1.2
                      }}
                    >
                      {stat.label}
                    </Typography>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        color: '#1e293b',
                        fontWeight: 700,
                        lineHeight: 1.2,
                        fontFamily: 'Monaco, Consolas, monospace',
                        fontSize: '1.1rem'
                      }}
                    >
                      {stat.value}
                    </Typography>
                  </Box>
                </Stack>
              </Box>
            ))}
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
}
