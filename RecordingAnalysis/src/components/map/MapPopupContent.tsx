"use client";
import React from "react";
import { Card, CardContent, Typography, Box, Stack, Divider } from "@mui/material";
import { Speed, AccessTime, Place, Navigation, Height, Timeline } from "@mui/icons-material";
import { TelemetryPoint, Coordinates } from "@/utils/types";

interface MapPopupContentProps {
  coords?: Coordinates;
  telemetryPoint?: TelemetryPoint;
  speed?: string;
  timestamp?: number;
  pointIndex?: number;
}

export const MapPopupContent: React.FC<MapPopupContentProps> = ({
  coords,
  telemetryPoint,
  speed,
  timestamp,
  pointIndex,
}) => {
  const longitude = telemetryPoint?.longitude || coords?.[0] || 0;
  const latitude = telemetryPoint?.latitude || coords?.[1] || 0;
  const altitude = telemetryPoint?.altitude;
  const actualSpeed = telemetryPoint?.speed?.toFixed(1) || speed || "N/A";
  const heading = telemetryPoint?.heading;
  const actualTimestamp = telemetryPoint?.timestamp || timestamp;
  
  const formatTime = (timestamp?: string | number) => {
    if (!timestamp) return "N/A";
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatCoordinate = (value: number, type: 'lat' | 'lng') => {
    const direction = type === 'lat' 
      ? (value >= 0 ? 'N' : 'S') 
      : (value >= 0 ? 'E' : 'W');
    return `${Math.abs(value).toFixed(6)}° ${direction}`;
  };

  return (
    <Card 
      sx={{ 
        minWidth: 300, 
        maxWidth: 340,
        borderRadius: 3,
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        boxShadow: '0 20px 40px rgba(0,0,0,0.12)',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
          color: 'white',
          p: 2.5,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Box 
          sx={{ 
            position: 'absolute',
            top: -20,
            right: -20,
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.05)',
            zIndex: 0
          }} 
        />
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ position: 'relative', zIndex: 1 }}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Box 
              sx={{ 
                p: 1,
                borderRadius: 2,
                background: 'rgba(255,255,255,0.15)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <Timeline sx={{ fontSize: 20 }} />
            </Box>
            <Box>
              <Typography variant="h6" fontWeight="700" sx={{ lineHeight: 1.2 }}>
                Waypoint {pointIndex || 'Data'}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Mission Telemetry
              </Typography>
            </Box>
          </Stack>
        </Stack>
      </Box>

      <CardContent sx={{ p: 0 }}>
        <Stack spacing={0}>
          {/* Position Section */}
          <Box sx={{ p: 2.5, background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)' }}>
            <Stack direction="row" alignItems="center" spacing={1.5} mb={2}>
              <Place sx={{ fontSize: 18, color: '#64748b' }} />
              <Typography 
                variant="subtitle2" 
                fontWeight="700" 
                sx={{ 
                  color: '#475569',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  fontSize: '0.75rem'
                }}
              >
                Geographic Position
              </Typography>
            </Stack>
            <Stack spacing={1.5}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                  Latitude
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'Monaco, Consolas, monospace', 
                    fontWeight: 600, 
                    color: '#1e293b',
                    background: 'rgba(255,255,255,0.8)',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    border: '1px solid #e2e8f0'
                  }}
                >
                  {formatCoordinate(latitude, 'lat')}
                </Typography>
              </Stack>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                  Longitude
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'Monaco, Consolas, monospace', 
                    fontWeight: 600, 
                    color: '#1e293b',
                    background: 'rgba(255,255,255,0.8)',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    border: '1px solid #e2e8f0'
                  }}
                >
                  {formatCoordinate(longitude, 'lng')}
                </Typography>
              </Stack>
              {altitude !== undefined && (
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                    Altitude
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={0.5}>
                    <Height sx={{ fontSize: 14, color: '#64748b' }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'Monaco, Consolas, monospace', 
                        fontWeight: 600, 
                        color: '#1e293b',
                        background: 'rgba(255,255,255,0.8)',
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        border: '1px solid #e2e8f0'
                      }}
                    >
                      {altitude.toFixed(1)} m
                    </Typography>
                  </Stack>
                </Stack>
              )}
            </Stack>
          </Box>

          <Divider sx={{ borderColor: '#e2e8f0' }} />

          {/* Motion Data */}
          <Box sx={{ p: 2.5, background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)' }}>
            <Stack direction="row" alignItems="center" spacing={1.5} mb={2}>
              <Speed sx={{ fontSize: 18, color: '#64748b' }} />
              <Typography 
                variant="subtitle2" 
                fontWeight="700" 
                sx={{ 
                  color: '#475569',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  fontSize: '0.75rem'
                }}
              >
                Motion Parameters
              </Typography>
            </Stack>
            <Stack spacing={1.5}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                  Velocity
                </Typography>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontFamily: 'Monaco, Consolas, monospace', 
                    fontWeight: 700, 
                    color: '#1e293b',
                    background: 'rgba(255,255,255,0.9)',
                    px: 1.5,
                    py: 0.5,
                    borderRadius: 1.5,
                    border: '1px solid #e2e8f0',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                  }}
                >
                  {actualSpeed} m/s
                </Typography>
              </Stack>
              {heading !== undefined && (
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                    Heading
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={0.5}>
                    <Navigation sx={{ fontSize: 14, color: '#64748b' }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'Monaco, Consolas, monospace', 
                        fontWeight: 600, 
                        color: '#1e293b',
                        background: 'rgba(255,255,255,0.9)',
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        border: '1px solid #e2e8f0'
                      }}
                    >
                      {heading.toFixed(1)}°
                    </Typography>
                  </Stack>
                </Stack>
              )}
            </Stack>
          </Box>

          {/* Timestamp */}
          {actualTimestamp && (
            <>
              <Divider sx={{ borderColor: '#e2e8f0' }} />
              <Box sx={{ p: 2.5, background: 'linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%)' }}>
                <Stack direction="row" alignItems="center" spacing={1.5} mb={1.5}>
                  <AccessTime sx={{ fontSize: 18, color: '#64748b' }} />
                  <Typography 
                    variant="subtitle2" 
                    fontWeight="700" 
                    sx={{ 
                      color: '#475569',
                      textTransform: 'uppercase',
                      letterSpacing: 0.5,
                      fontSize: '0.75rem'
                    }}
                  >
                    Temporal Data
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 500 }}>
                    Recorded At
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontFamily: 'Monaco, Consolas, monospace', 
                      fontWeight: 600, 
                      color: '#1e293b',
                      background: 'rgba(255,255,255,0.9)',
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      border: '1px solid #e2e8f0'
                    }}
                  >
                    {formatTime(actualTimestamp)}
                  </Typography>
                </Stack>
              </Box>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};
