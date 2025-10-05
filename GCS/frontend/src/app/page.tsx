"use client";
import { useState, useEffect } from 'react';
import HUD from '../components/HUD/HUD';
import InfoDashBoard from '../components/InfoDashboard/InfoDashBoard';

export default function Home() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showHUDElements, setShowHUDElements] = useState(true);
  const [isRecording, setIsRecording] = useState(false);

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
        <HUD showHUDElements={showHUDElements} isRecording={isRecording} />
      </div>
      
      {!isFullscreen && (
        <div className="h-[35vh] w-full bg-black">
          <InfoDashBoard 
              showHUDElements={showHUDElements} 
              setShowHUDElements={setShowHUDElements}
              isRecording={isRecording}
              setIsRecording={setIsRecording}
          />
        </div>
      )}
    </div>
  );
}