'use client';
import React, { useState, useEffect } from 'react';
import {Box, Typography, Card, CircularProgress, Alert} from '@mui/material';
import axios from 'axios';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import MapIcon from '@mui/icons-material/Map';
import InsightsIcon from '@mui/icons-material/Insights';

interface RecordedObject {
  objectID: string;
  classification: string;
  timestamp: string;
}

export const LandingPage: React.FC = () => {
  const [objects, setObjects] = useState<RecordedObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchObjects = async () => {
      try {
        const { data } = await axios.get('http://localhost:9875/all_objects');
        setObjects(data);
      } catch (err) {
        console.error('Error fetching objects:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch objects');
      } finally {
        setLoading(false);
      }
    };
    fetchObjects();
  }, []);

  const handleObjectClick = (id: string) => {
    window.location.href = `${window.location.origin}?objectId=${id}`;
  };

  const formatTimestamp = (timestamp: string) =>
    new Date(timestamp).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });

const ObjectCard = ({ obj }: { obj: RecordedObject }) => (
  <Card
    onClick={() => handleObjectClick(obj.objectID)}
    sx={{
      p: 2.2,
      borderRadius: 3,
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      boxShadow: '0 3px 10px rgba(0,0,0,0.04)',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      maxWidth: 260,
      mx: 'auto',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: '0 6px 18px rgba(14,165,233,0.15)',
        borderColor: '#0ea5e9',
      },
    }}
  >
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
      <FlightTakeoffIcon sx={{ fontSize: 20, color: '#0ea5e9', mr: 1 }} />
      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0f172a' }}>
        {obj.classification}
      </Typography>
    </Box>

    <Typography
      variant="body2"
      sx={{ color: '#475569', mb: 0.5, fontSize: '0.8rem' }}
    >
      Recorded on
    </Typography>

    <Typography
      variant="body2"
      sx={{ fontWeight: 500, color: '#1e293b', fontSize: '0.8rem' }}
    >
      {formatTimestamp(obj.timestamp)}
    </Typography>
  </Card>
);


  return (
    <Box sx={{ bgcolor: '#f8fafc', minHeight: '100vh' }}>
      {/* Hero Section */}
      <Box
        sx={{
          textAlign: 'center',
          py: { xs: 8, md: 10 },
          px: 2,
          background: 'linear-gradient(135deg, #1e3a8a, #0ea5e9)',
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.15) 0%, transparent 70%)',
          }}
        />
        <Typography
          variant="h2"
          sx={{ fontWeight: 800, zIndex: 2, position: 'relative', mb: 2 }}
        >
          LOCK2A Analysis Platform
        </Typography>
        <Typography
          variant="h6"
          sx={{ maxWidth: 650, mx: 'auto', opacity: 0.9, mb: 4, zIndex: 2, position: 'relative' }}
        >
          Analyze, visualize, and replay drone missions with high-fidelity trajectory mapping and
          telemetry insights.
        </Typography>
      </Box>

      {/* Features Section */}
      <Box sx={{ py: { xs: 4, md: 6 }, px: { xs: 3, md: 8 }, backgroundColor: '#fff' }}>
        <Box sx={{ 
          display: 'grid', 
          gap: 4,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
          justifyItems: 'center'
        }}>
          {[
            {
              icon: <FlightTakeoffIcon sx={{ fontSize: 40, color: '#0ea5e9' }} />,
              title: 'Flight Tracking',
              desc: 'Visualize precise drone paths across missions in 3D space.',
            },
            {
              icon: <MapIcon sx={{ fontSize: 40, color: '#0ea5e9' }} />,
              title: 'Terrain Integration',
              desc: 'Overlay trajectory data on detailed satellite and terrain imagery.',
            },
            {
              icon: <InsightsIcon sx={{ fontSize: 40, color: '#0ea5e9' }} />,
              title: 'Mission Insights',
              desc: 'Extract key stats like altitude, duration, and speed analytics.',
            }
          ].map((feature, i) => (
            <Box key={i} sx={{ textAlign: 'center', maxWidth: 300 }}>
              <Card
                sx={{
                  p: 2,
                  borderRadius: 4,
                  textAlign: 'center',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.05)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 32px rgba(14,165,233,0.2)',
                  },
                }}
              >
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0f172a' }}>
                  {feature.title}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>
                  {feature.desc}
                </Typography>
              </Card>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Available Recordings Section */}
      <Box sx={{ px: { xs: 3, md: 8 }, pb: 6, py: 6 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            textAlign: 'center',
            mb: 4,
            color: '#0f172a',
          }}
        >
          Available Recordings
        </Typography>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress size={40} sx={{ color: '#0ea5e9' }} />
          </Box>
        )}

        {error && <Alert severity="error">{error}</Alert>}

        {!loading && !error && objects.length === 0 && (
          <Alert severity="info">No recordings found in the database.</Alert>
        )}

        {!loading && !error && objects.length > 0 && (
          <Box
            sx={{
              display: 'grid',
              gap: 2.5,
              justifyContent: 'center',
              gridTemplateColumns: {
                xs: 'repeat(auto-fit, minmax(180px, 1fr))',
                sm: 'repeat(auto-fit, minmax(200px, 1fr))',
                md: 'repeat(auto-fit, minmax(220px, 1fr))',
              },
            }}
          >
            {objects.map((obj) => (
              <Box key={obj.objectID}>
                <ObjectCard obj={obj} />
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* Footer */}
      <Box
        sx={{
          textAlign: 'center',
          py: 3,
          background: '#f1f5f9',
          color: '#475569',
          fontSize: '0.9rem',
        }}
      >
        © {new Date().getFullYear()} LOCK2A
      </Box>
    </Box>
  );
};
