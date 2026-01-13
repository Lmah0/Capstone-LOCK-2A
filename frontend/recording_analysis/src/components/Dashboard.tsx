"use client";
import React from 'react';
import { useRouter } from 'next/navigation';
import { AppBar, Toolbar, Typography, Box, Stack, Avatar, Button } from '@mui/material';
import { Flight } from '@mui/icons-material';

export default function Dashboard() {
  const router = useRouter();

  const handleBackClick = () => {
    router.push('/'); // navigates back to landing page
  };

  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{ 
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        borderBottom: '2px solid #e2e8f0',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}
    >
      <Toolbar sx={{ minHeight: '80px !important', px: 3, justifyContent: 'space-between' }}>
        {/* Left Section */}
        <Stack direction="row" alignItems="center" spacing={2}>
          <Avatar 
            sx={{ 
              bgcolor: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', 
              color: 'white',
              width: 48,
              height: 48,
              background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            <Flight fontSize="large" />
          </Avatar>
          
          <Box>
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                fontWeight: 700,
                color: '#1e293b',
                letterSpacing: '-0.5px',
                background: 'linear-gradient(135deg, #1e293b 0%, #3b82f6 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              LOCK-2A Ground Control System
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#64748b',
                fontWeight: 500
              }}
            >
              Real-time Trajectory Analysis & Mission Monitoring
            </Typography>
          </Box>
        </Stack>

        {/* Right Section — Back Button */}
        <Button 
          variant="outlined" 
          onClick={handleBackClick}
          sx={{
            borderColor: '#3b82f6',
            color: '#1d4ed8',
            fontWeight: 600,
            textTransform: 'none',
            '&:hover': {
              backgroundColor: 'rgba(59,130,246,0.08)',
              borderColor: '#1d4ed8'
            }
          }}
        >
          ← Back
        </Button>
      </Toolbar>
    </AppBar>
  );
}