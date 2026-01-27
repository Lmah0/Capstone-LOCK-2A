"use client";
import { useState, useEffect } from 'react';
import HUD from '../components/HUD/HUD';
import InfoDashBoard from '../components/InfoDashBoard/InfoDashBoard';

export default function Home() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showHUDElements, setShowHUDElements] = useState(true);
  const [isMetric, setIsMetric] = useState(true);
  const [pinnedTelemetry, setPinnedTelemetry] = useState<string[]>(['speed', 'altitude', 'latitude', 'longitude']);
  const [followDistance, setFollowDistance] = useState(20.0);
  const [flightMode, setFlightMode] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  // Load pinned telemetry from localStorage on component mount
  useEffect(() => {
    const saved = localStorage.getItem('pinnedTelemetry');
    if (saved) {
      setPinnedTelemetry(JSON.parse(saved));
    }
  }, []);

  // Save pinned telemetry to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('pinnedTelemetry', JSON.stringify(pinnedTelemetry));
  }, [pinnedTelemetry]);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+F (Mac) or Ctrl+F (Windows/Linux)
      if ((event.metaKey || event.ctrlKey) && event.key === 'f') {
        event.preventDefault();
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isFullscreen]);

  return (
    <div className="font-sans min-h-screen w-full flex flex-col bg-black">
      <div className={`w-full bg-neutral-900 ${isFullscreen ? 'h-screen' : 'h-[65vh]'} ${!isFullscreen ? 'border-b border-neutral-800' : ''}`}>
        <HUD
            isRecording={isRecording}
            showHUDElements={showHUDElements} 
            pinnedTelemetry={pinnedTelemetry} 
            isMetric={isMetric} 
            followDistance={followDistance}
            flightMode={flightMode}
        />
      </div>
      
      {!isFullscreen && (
        <div className="h-[35vh] w-full bg-black">
          <InfoDashBoard 
              isRecording={isRecording}
              setIsRecording={setIsRecording}
              showHUDElements={showHUDElements} 
              setShowHUDElements={setShowHUDElements}
              isMetric={isMetric}
              setIsMetric={setIsMetric}
              pinnedTelemetry={pinnedTelemetry}
              setPinnedTelemetry={setPinnedTelemetry}
              followDistance={followDistance}
              setFollowDistance={setFollowDistance}
              flightMode={flightMode}
              setFlightMode={setFlightMode}
          />
        </div>
      )}
    </div>
  );
}