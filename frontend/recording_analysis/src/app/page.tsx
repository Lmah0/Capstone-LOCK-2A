'use client';
import React, { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { LandingPage } from '../components/LandingPage';
import { AnalysisView } from '../components/AnalysisView';

export default function HomePage() {
  const [isClient, setIsClient] = useState(false);

  // Handle client-side hydration
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Check if we should show the landing page (only after client hydration)
  const urlParams = isClient ? new URLSearchParams(window.location.search) : null;
  const objectId = urlParams?.get('objectId');
  const showLandingPage = isClient && !objectId;

  // Show loading during hydration to prevent layout shift
  if (!isClient) {
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
        <CircularProgress size={32} sx={{ color: '#6366f1' }} />
      </Box>
    );
  }

  if (showLandingPage) {
    return <LandingPage />;
  }

  // Show the analysis view if we have an objectId
  if (objectId) {
    return <AnalysisView objectId={objectId} />;
  }
}