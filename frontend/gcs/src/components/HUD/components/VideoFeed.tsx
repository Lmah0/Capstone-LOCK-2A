import React, { useState, useEffect, useRef, useCallback } from 'react';

export default function VideoFeed() {
    const backendPort = 8766;
    const videoUrl = `http://localhost:${backendPort}/video_feed`;
    const gcsServerUrl = `ws://localhost:${backendPort}/ws/gcs`;
    
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isTracking, setIsTracking] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const imgRef = useRef<HTMLImageElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    
    // High-performance mouse tracking using refs instead of state
    const lastMouseMoveTimeRef = useRef<number>(0);
    const pendingMouseMoveRef = useRef<{ x: number; y: number } | null>(null);
    const MOUSE_THROTTLE_MS = 80;  // throttle to 80ms for better performance

    // WebSocket connection
    useEffect(() => {
        const connectWebSocket = () => {
            try {
                const ws = new WebSocket(gcsServerUrl);

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    setIsStreaming(true);
                };

                ws.onclose = () => {
                    console.log('WebSocket disconnected, reconnecting...');
                    setIsStreaming(false);
                    setTimeout(connectWebSocket, 3000);
                };

                ws.onerror = (error) => {
                    setIsStreaming(false);
                    setError('WebSocket connection error');
                };


                wsRef.current = ws;
            } catch (error) {
                console.error('Failed to connect WebSocket:', error);
                setIsStreaming(false);
                setTimeout(connectWebSocket, 3000);
            }
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const handleMouseMove = useCallback((e: React.MouseEvent<HTMLImageElement>) => {
        if (!imgRef.current) return;

        const now = Date.now();
        if (now - lastMouseMoveTimeRef.current < MOUSE_THROTTLE_MS) {
            // Still update pending position even if we don't send yet
            const rect = imgRef.current.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);
            const scaleX = imgRef.current.naturalWidth / rect.width;
            const scaleY = imgRef.current.naturalHeight / rect.height;
            pendingMouseMoveRef.current = {
                x: Math.round(x * scaleX),
                y: Math.round(y * scaleY)
            };
            return;
        }
        
        lastMouseMoveTimeRef.current = now;

        const rect = imgRef.current.getBoundingClientRect();
        const x = Math.round(e.clientX - rect.left);
        const y = Math.round(e.clientY - rect.top);
        const scaleX = imgRef.current.naturalWidth / rect.width;
        const scaleY = imgRef.current.naturalHeight / rect.height;
        const actualX = Math.round(x * scaleX);
        const actualY = Math.round(y * scaleY);

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'mouse_move',
                x: actualX,
                y: actualY
            }));
        }
    }, []);

    // Send click event to backend
    const handleClick = useCallback((e: React.MouseEvent<HTMLImageElement>) => {
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
    }, []);

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
        <div className="w-full h-full relative bg-gray-900">
            <div ref={containerRef} className="relative w-full h-full bg-gray-800 overflow-hidden">
                {error ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center w-full h-full text-red-400 p-8 text-center bg-gray-900/90">
                        <svg id='error-svg' className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path>
                        </svg>
                        <p className="font-semibold">{error}</p>
                        <p className="text-sm mt-2 text-gray-400">Ensure servers & tracking algorithm are running.</p>
                    </div>
                ) : (
                    <img
                        ref={imgRef}
                        src={videoUrl}
                        alt="Live AI processed video stream"
                        className={`absolute inset-0 w-full h-full object-cover cursor-crosshair ${isStreaming ? 'opacity-100' : 'opacity-50'}`}
                        onError={() => {
                            setIsStreaming(false);
                            setError("Stream error. Is the Python server running?");
                        }}
                        onMouseMove={handleMouseMove}
                        onClick={handleClick}
                    />
                )}

                {!isStreaming && !error && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm z-10">
                        <svg className="animate-spin h-8 w-8 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="ml-3 text-white">Connecting to stream...</span>
                    </div>
                )}
            </div>
        </div>
    );
}