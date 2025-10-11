'use client';
import { createContext, useContext, useState, useEffect, ReactNode, useRef, useCallback } from 'react';

interface WebSocketContextType {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: string) => void;
  subscribe: (dataTypes: string[]) => void;
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
  const [telemetryData, setTelemetryData] = useState<any>(null);
  const [batteryData, setBatteryData] = useState<any>(null);
  const [droneConnection, setDroneConnection] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
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
        switch (data.type) {
          case 'telemetry':
            setTelemetryData(data);
            break;
          case 'battery':
            setBatteryData(data);
            break;
          case 'connection':
            setDroneConnection(data.connected);
            break;
          case 'subscription_confirmed':
            console.log('Subscribed to:', data.dataTypes);
            break;
          default:
            console.log('Unknown message type:', data.type);
        }
      } catch (error) {
        console.log('Received text:', event.data);
      }
    };

    websocket.onclose = () => {
      console.log('🔌 Disconnected');
      setConnectionStatus('disconnected');
      
      // Try to reconnect after 1 second
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        console.log(`🔄 Attempting Reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
        
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

  const subscribe = useCallback((dataTypes: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const subscriptionMessage = {
        type: 'subscribe',
        dataTypes: dataTypes
      };
      wsRef.current.send(JSON.stringify(subscriptionMessage));
      console.log('Subscribing to:', dataTypes);
    }
  }, []);

  useEffect(() => {
    connect(); 
    return () => {
      // Clear reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const value: WebSocketContextType = { connectionStatus, sendMessage, subscribe, telemetryData, batteryData, droneConnection };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}