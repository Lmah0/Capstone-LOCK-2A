'use client';
import { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { TelemetryData } from '@/utils/telemetryConfig';

interface WebSocketContextType {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: string) => void;
  telemetryData: any;
  batteryData: any;
  droneConnection: boolean;
  setIsRecording: React.Dispatch<React.SetStateAction<boolean>>;
  isRecording: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [batteryData, setBatteryData] = useState<any>(null);
  const [droneConnection, setDroneConnection] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const isRecordingRef = useRef<boolean>(false);
  const recordedDataRef = useRef<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const droneTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    const wasRecording = isRecordingRef.current;
    isRecordingRef.current = isRecording;
    
    // If we just stopped recording, send the collected data
    if (wasRecording && !isRecording && recordedDataRef.current.length > 0) {
      console.log(`Sending ${recordedDataRef.current.length} recorded data points to backend`);
      sendMessage(JSON.stringify({ type: "record", data: { recordingData: recordedDataRef.current }}));
      recordedDataRef.current = [];
    }
    
    // If we just started recording, clear any existing data
    if (!wasRecording && isRecording) {
      recordedDataRef.current = [];
      console.log("Started recording telemetry data");
    }
  }, [isRecording]);

  const connect = () => {
    // Don't try to connect if already connecting or connected
    if (connectionStatus === 'connecting' || connectionStatus === 'connected') {
      return;
    }

    // Stop trying after max attempts
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      setConnectionStatus('error');
      return;
    }

    setConnectionStatus('connecting');
    console.log(`Connecting... (attempt ${reconnectAttempts.current + 1})`);
    
    const websocket = new WebSocket('ws://localhost:8766/ws/gcs');
    wsRef.current = websocket;

    websocket.onopen = () => {
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);    
        if (data) {
          if(data.status)
          {
            // Do not process status messages further to avoid re-render on status acknowledgment
            console.log("Status message from server:", data.status);
            return;
          }
          // Update telemetry data
          setTelemetryData({ 
              speed: data.speed,
              altitude: data.altitude,
              latitude: data.latitude,
              longitude: data.longitude,
              heading: data.heading,
              roll: data.roll,
              pitch: data.pitch,
              yaw: data.yaw });
          
          if (data.battery_voltage && data.battery_remaining) {
            setBatteryData({
              percentage: data.battery_remaining,
              usage: data.battery_voltage
            });
          }
          
          // Connection is considered active if we're receiving telemetry
          setDroneConnection(true);
          
          // Reset drone connection timeout - if we don't receive data for 5 seconds, mark as disconnected
          if (droneTimeoutRef.current) {
            clearTimeout(droneTimeoutRef.current);
          }
          droneTimeoutRef.current = setTimeout(() => {
            setDroneConnection(false);
          }, 5000);
          
          // Collect data while recording
          if (isRecordingRef.current) {
            recordedDataRef.current.push({...data});
          }
        }
      } catch (error) {
        console.log('Received text:', event.data);
      }
    };

    websocket.onclose = () => {
      setConnectionStatus('disconnected');  
      // Try to reconnect after 1 second
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        console.log(`Attempting Reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 1000);
      }
    };

    websocket.onerror = (error) => {
      setConnectionStatus('error');
    };
  };

  const sendMessage = (message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  };

  useEffect(() => {
    connect(); 
    return () => {
      // Clear timeouts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (droneTimeoutRef.current) {
        clearTimeout(droneTimeoutRef.current);
      }
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const value: WebSocketContextType = { 
    connectionStatus, 
    sendMessage,
    telemetryData, 
    batteryData, 
    droneConnection,
    setIsRecording,
    isRecording
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}