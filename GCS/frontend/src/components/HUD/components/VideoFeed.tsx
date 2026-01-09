import React, { useState, useEffect, useRef } from 'react';

export default function VideoFeed() {
    const backendPort = 8766;
    const videoUrl = `http://localhost:${backendPort}/video_feed`;
    const wsUrl = `ws://localhost:${backendPort}/ws/gcs`;

    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [isTracking, setIsTracking] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const imgRef = useRef<HTMLImageElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // WebSocket connection
    useEffect(() => {
        const connectWebSocket = () => {
            try {
                const ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    setWsConnected(true);
                };

                ws.onclose = () => {
                    console.log('WebSocket disconnected, reconnecting...');
                    setWsConnected(false);
                    setTimeout(connectWebSocket, 3000);
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };

                ws.onmessage = (event) => {
                    // Handle messages from backend (telemetry, status updates, etc.)
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Received:', data);
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                    }
                };

                wsRef.current = ws;
            } catch (error) {
                console.error('Failed to connect WebSocket:', error);
                setTimeout(connectWebSocket, 3000);
            }
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [wsUrl]);

    // Check video stream status
    useEffect(() => {
        const checkStream = () => {
            const img = new Image();
            img.onload = () => {
                setIsStreaming(true);
                setError(null);
            };
            img.onerror = () => {
                setIsStreaming(false);
                setError("Stream error. Is the Python server running?");
            };
            img.src = `${videoUrl}?t=${Date.now()}`;
        };

        const interval = setInterval(checkStream, 5000);
        checkStream();

        return () => clearInterval(interval);
    }, [videoUrl]);

    // Send mouse move events to backend
    const handleMouseMove = (e: React.MouseEvent<HTMLImageElement>) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (!imgRef.current) return;

        const rect = imgRef.current.getBoundingClientRect();
        const x = Math.round(e.clientX - rect.left);
        const y = Math.round(e.clientY - rect.top);

        // Scale coordinates to actual image dimensions
        const scaleX = imgRef.current.naturalWidth / rect.width;
        const scaleY = imgRef.current.naturalHeight / rect.height;
        const actualX = Math.round(x * scaleX);
        const actualY = Math.round(y * scaleY);

        wsRef.current.send(JSON.stringify({
            type: 'mouse_move',
            x: actualX,
            y: actualY
        }));
    };

    // Send click event to backend
    const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (!imgRef.current) return;

        const rect = imgRef.current.getBoundingClientRect();
        const x = Math.round(e.clientX - rect.left);
        const y = Math.round(e.clientY - rect.top);

        // Scale coordinates to actual image dimensions
        const scaleX = imgRef.current.naturalWidth / rect.width;
        const scaleY = imgRef.current.naturalHeight / rect.height;
        const actualX = Math.round(x * scaleX);
        const actualY = Math.round(y * scaleY);

        wsRef.current.send(JSON.stringify({
            type: 'click',
            x: actualX,
            y: actualY
        }));

        setIsTracking(true);
        console.log(`Clicked at (${actualX}, ${actualY})`);
    };

    // Stop tracking
    const handleStopTracking = () => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({
            type: 'stop_tracking'
        }));

        setIsTracking(false);
        console.log('Stopped tracking');
    };

    // Reselect object
    const handleReselectObject = () => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({
            type: 'reselect_object'
        }));

        setIsTracking(false);
        console.log('Reselect object');
    };

    return (
        <div className="flex flex-col items-center justify-center w-full h-full bg-gray-900 p-4">
            <div className="flex items-center justify-between w-full max-w-4xl mb-4">
                <h1 className="text-xl font-bold text-white">AI Object Tracking</h1>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm text-gray-400">
                        {wsConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>

            <div ref={containerRef} className="relative w-full max-w-4xl aspect-video bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
                {error ? (
                    <div className="flex flex-col items-center justify-center w-full h-full text-red-400 p-8 text-center">
                        <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path>
                        </svg>
                        <p className="font-semibold">{error}</p>
                        <p className="text-sm mt-2 text-gray-400">Ensure servers & tracking algorithm are running.</p>
                    </div>
                ) : (
                    <img
                        ref={imgRef}
                        key={videoUrl}
                        src={videoUrl}
                        alt="Live AI processed video stream"
                        className={`w-full h-full object-contain transition-opacity duration-500 cursor-crosshair ${isStreaming ? 'opacity-100' : 'opacity-50'}`}
                        onError={() => setIsStreaming(false)}
                        onMouseMove={handleMouseMove}
                        onClick={handleClick}
                    />
                )}

                {!isStreaming && !error && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800/80 backdrop-blur-sm">
                        <svg className="animate-spin h-8 w-8 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="ml-3 text-white">Connecting to stream...</span>
                    </div>
                )}
            </div>

            {/* Control Buttons
            <div className="flex gap-4 mt-6">
                <button
                    onClick={handleStopTracking}
                    disabled={!isTracking || !wsConnected}
                    className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                        isTracking && wsConnected
                            ? 'bg-red-600 hover:bg-red-700 text-white cursor-pointer'
                            : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    }`}
                >
                    Stop Tracking
                </button>
                <button
                    onClick={handleReselectObject}
                    disabled={!isTracking || !wsConnected}
                    className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                        isTracking && wsConnected
                            ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
                            : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    }`}
                >
                    Reselect Object
                </button>
            </div> */}
        </div>
    );
}