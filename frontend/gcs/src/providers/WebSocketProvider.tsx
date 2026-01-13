'use client';
import { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { TelemetryData } from '@/utils/telemetryConfig';

interface WebSocketContextType {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: string) => void;
  telemetryData: any;
  batteryData: any;
  droneConnection: boolean;
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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const droneTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

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
    
    const websocket = new WebSocket('ws://localhost:8766/ws/gcs');
    wsRef.current = websocket;

    websocket.onopen = () => {
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);    
        if (data) 
        {
          if(data.status)
          {
            if(data.status !== 200) {
              console.log('Error from server:', data.error || 'Unknown error');
            }
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
    droneConnection
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}