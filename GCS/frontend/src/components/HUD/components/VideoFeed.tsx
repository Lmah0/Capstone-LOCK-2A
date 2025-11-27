import React, { useState, useEffect } from 'react';

export default function VideoFeed() {
    const backendPort = 8766;
    const videoUrl = `http://localhost:${backendPort}/video_feed`;
    console.log(videoUrl)
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Effect to check if the image source is loading/working
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
            // Append a timestamp to prevent caching, forcing the browser to hit the endpoint
            img.src = `${videoUrl}?t=${Date.now()}`;
        };

        // Check the stream status every few seconds
        const interval = setInterval(checkStream, 5000); 

        checkStream();

        return () => clearInterval(interval);
    }, [videoUrl]);

    return (
        <div className="flex flex-col items-center justify-center w-full h-full bg-gray-900 p-4">
            <h1 className="text-xl font-bold text-white mb-4">Video Feed</h1>
            <div className="relative w-full max-w-4xl aspect-video bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
                {error ? (
                    <div className="flex flex-col items-center justify-center w-full h-full text-red-400 p-8 text-center">
                        <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>
                        <p className="font-semibold">{error}</p>
                        <p className="text-sm mt-2 text-gray-400">Ensure servers & tracking algorithm are running.</p>
                    </div>
                ) : (
                    // The browser continuously updates the <img> src
                    <img 
                        // Use a key to force the image element to re-render if the URL changes (MJPEG stream will also help to handle continuous refresh)
                        key={videoUrl}
                        src={videoUrl}
                        alt="Live AI processed video stream"
                        className={`w-full h-full object-contain transition-opacity duration-500 ${isStreaming ? 'opacity-100' : 'opacity-50'}`}
                        // Fallback message while loading
                        onError={() => setIsStreaming(false)}
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
        </div>
    );
}