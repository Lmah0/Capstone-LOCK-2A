import ConnectionStatus from './components/ConnectionStatus';
import Battery from './components/Battery';
import VideoFeed from './components/VideoFeed';
import TelemetryData from './components/TelemetryData';
import Heading from './components/Heading';
import FlightMode from './components/FlightMode';

export default function HUD() {

    return (
        <div className="w-full h-full relative">
            <VideoFeed />
            
            {/* HUD Area Overlay */}
            <div className="absolute inset-2 pointer-events-none z-5">
                <div className="w-full h-full border border-white/20 bg-black/10 rounded-xl"></div>
            </div>
            
            <div className="absolute top-4 left-4 z-10">
                <ConnectionStatus />
            </div>
            <div className="absolute bottom-4 right-4 z-10">
                <TelemetryData/>
            </div>
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
                <Heading />
            </div>
            <div className="absolute bottom-4 left-4 z-10">
                <FlightMode />
            </div>
            <div className="absolute top-4 right-4 z-10">
                <Battery />
            </div>
        </div>
    );
}
