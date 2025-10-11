import ConnectionStatus from './components/ConnectionStatus';
import ServerConnection from './components/ServerConnection';
import BatteryGuage from './components/Battery';
import VideoFeed from './components/VideoFeed';
import TelemetryData from './components/TelemetryData';
import Heading from './components/Heading';
import FlightMode from './components/FlightMode';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';

interface HUDProps {
    showHUDElements: boolean;
    isRecording: boolean;
    pinnedTelemetry: string[];
    isMetric: boolean;
    followDistance: number;
    flightMode: string;
}

export default function HUD({ showHUDElements, isRecording, pinnedTelemetry, isMetric, followDistance, flightMode }: HUDProps) {

    return (
        <div className="w-full h-full relative">
            <VideoFeed />
            
        <div className="absolute top-4 left-4 z-50">
            <ServerConnection />
        </div>
        <div className="absolute top-10 left-4 z-10">
            <ConnectionStatus isConnected={false} />
        </div>
            {isRecording && (
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 flex items-center space-x-1 px-2 py-1">
                    <RadioButtonCheckedIcon className="text-red-600 animate-pulse" />
                </div>
            )}
        {/* HUD Area Overlay */}
        {showHUDElements && (
            <>
                <div className="absolute inset-2 pointer-events-none z-5">
                    <div className="w-full h-full border border-white/20 bg-black/10 rounded-xl"></div>
                </div>
                
                <div className="absolute bottom-4 right-4 z-10">
                    <TelemetryData pinnedTelemetry={pinnedTelemetry} isMetric={isMetric} />
                </div>
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
                    <Heading />
                </div>
                <div className="absolute bottom-4 left-4 z-10">
                    <FlightMode isMetric={isMetric} followDistance={followDistance} flightMode={flightMode} />
                </div>
                <div className="absolute top-4 right-4 z-10">
                    <BatteryGuage />
                </div>
            </>
        )}
        </div>
    );
}