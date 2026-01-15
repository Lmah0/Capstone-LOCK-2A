"use client";
import React from "react";
import { Card, CardContent, Typography, Button, Stack } from "@mui/material";
import { PlayArrow, Pause, Replay, Settings, SkipNext } from "@mui/icons-material";

interface ControlPanelProps {
  onReplay: () => void;
  onPauseResume: () => void;
  onSkip: () => void;
  isPlaying: boolean;
  isCompleted: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({onReplay, onPauseResume, onSkip, isPlaying, isCompleted}) => {
  const getButtonText = () => {
    if (isCompleted) return 'Replay';
    if (isPlaying) return 'Pause';
    return 'Resume';
  };

  const getButtonIcon = () => {
    if (isCompleted) return <PlayArrow />;
    if (isPlaying) return <Pause />;
    return <PlayArrow />;
  };

  return (
    <Card
      id='control-panel'
      sx={{ 
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: 3,
        boxShadow: '0 8px 25px rgba(0,0,0,0.08)',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 12px 35px rgba(0,0,0,0.12)',
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 700,
            color: '#1e293b',
            mb: 1.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}
        >
          <Settings sx={{ color: '#3b82f6' }} />
          Mission Control
        </Typography>

        <Stack spacing={2} sx={{ mb: 2 }}>
          <Button
            id='restart-mission-button'
            variant="contained"
            startIcon={<Replay />}
            onClick={onReplay}
            fullWidth
            sx={{ 
              textTransform: 'none',
              fontWeight: 600,
              py: 1.5,
              background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #2563eb 0%, #1e40af 100%)',
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(59, 130, 246, 0.4)'
              },
              borderRadius: 2,
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)',
              transition: 'all 0.2s ease'
            }}
          >
            Restart Mission
          </Button>
          
          {/* Pause/Resume and Skip buttons side by side */}
          <Stack direction="row" spacing={1.5}>
            <Button
              id='pause-resume-button'
              variant="outlined"
              startIcon={getButtonIcon()}
              onClick={onPauseResume}
              fullWidth
              sx={{ 
                textTransform: 'none',
                fontWeight: 600,
                py: 1.5,
                borderWidth: 2,
                borderColor: '#3b82f6',
                color: '#3b82f6',
                borderRadius: 2,
                background: 'rgba(59, 130, 246, 0.05)',
                '&:hover': {
                  borderWidth: 2,
                  borderColor: '#2563eb',
                  background: 'rgba(59, 130, 246, 0.1)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 15px rgba(59, 130, 246, 0.2)'
                },
                transition: 'all 0.2s ease'
              }}
            >
              {getButtonText()}
            </Button>

            {/* Skip Animation Button - only show when animation is in progress and not completed */}
            {(isPlaying) && !isCompleted && onSkip && (
              <Button
                id='skip-animation-button'
                variant="outlined"
                startIcon={<SkipNext />}
                onClick={onSkip}
                fullWidth
                sx={{ 
                  textTransform: 'none',
                  fontWeight: 600,
                  py: 1.5,
                  borderWidth: 2,
                  borderColor: '#f59e0b',
                  color: '#f59e0b',
                  borderRadius: 2,
                  background: 'rgba(245, 158, 11, 0.05)',
                  '&:hover': {
                    borderWidth: 2,
                    borderColor: '#d97706',
                    background: 'rgba(245, 158, 11, 0.1)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 15px rgba(245, 158, 11, 0.2)'
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                Skip
              </Button>
            )}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};
