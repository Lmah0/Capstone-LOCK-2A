import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HUD from '../src/components/HUD/HUD';
import { useWebSocket } from '../src/providers/WebSocketProvider';
import { mock } from 'node:test';

// Mock the WebSocketProvider at the top level
jest.mock('../src/providers/WebSocketProvider', () => ({
  useWebSocket: jest.fn(),
  sendMessage: jest.fn()
}));

const mockProps = {
  showHUDElements: true,
  isRecording: false,
  pinnedTelemetry: [],
  isMetric: false,
  followDistance: 10,
  flightMode: 'MANUAL'
};

test('HUD Component Disconnected Drone, Disconnected Server', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  render(<HUD {...mockProps} />);

  // Test that the main container exists
  const container = document.querySelector('.w-full.h-full.relative');
  expect(container).toBeInTheDocument();

  // Test that the component renders key HUD elements
  expect(screen.getByText('Loading telemetry...')).toBeInTheDocument();
  expect(screen.getByText('Disconnected')).toBeInTheDocument();

  // Test for ErrorIcon existence - drone is disconnected so error should be present
  expect(screen.getByTestId('drone-disconnected')).toBeInTheDocument();
  expect(screen.getByLabelText('Vehicle connection has been lost')).toBeInTheDocument();

  // Overlay should be red when drone is disconnected
  const overlay = document.getElementById('overlay');
  expect(overlay).toBeInTheDocument();
  expect(overlay?.className).toContain('bg-red-500/10');
  expect(overlay?.className).toContain('border-red-500/80');
});

test('HUD Component Connected Drone, Connected Server', () => {
  useWebSocket.mockReturnValue({connectionStatus: 'connected', droneConnection: true, telemetryData: null});
  render(<HUD {...mockProps} />);

  // Test that the main container exists
  const container = document.querySelector('.w-full.h-full.relative');
  expect(container).toBeInTheDocument();

  expect(screen.getByText('Loading telemetry...')).toBeInTheDocument();
  // Test that the server disconnection status is shown
  expect(screen.getByText('Connected')).toBeInTheDocument();

  // Drone is connected, so ErrorIcon should not be present
  expect(screen.queryByTestId('drone-disconnected')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Vehicle connection has been lost')).not.toBeInTheDocument();
});

