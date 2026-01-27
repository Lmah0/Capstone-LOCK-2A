import { render, screen, cleanup, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HUD from '../src/components/HUD/HUD';
import { useWebSocket } from '../src/providers/WebSocketProvider';
import * as cpb from 'react-circular-progressbar'; // import to spy on buildStyles
import axios from 'axios';

jest.mock('axios');
// Mock the WebSocketProvider at the top level
jest.mock('../src/providers/WebSocketProvider', () => ({
  useWebSocket: jest.fn(),
  sendMessage: jest.fn()
}));

// Mock console errors for now to reduce noise during tests
console.error = jest.fn();

// Mock RTCPeerConnection for WebRTC tests
global.RTCPeerConnection = jest.fn(() => ({
  createOffer: jest.fn().mockResolvedValue({ sdp: 'mock-offer', type: 'offer' }),
  setLocalDescription: jest.fn().mockResolvedValue(undefined),
  setRemoteDescription: jest.fn().mockResolvedValue(undefined),
  addTransceiver: jest.fn().mockReturnValue({}),
  close: jest.fn(),
  onconnectionstatechange: null,
  ontrack: null,
  iceGatheringState: 'complete',
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  connectionState: 'connected'
}));

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  useWebSocket.mockReturnValue({
    connectionStatus: 'connected',
    droneConnection: true,
    telemetryData: null,
    batteryData: null,
    trackingData: { tracking: false, tracked_class: null }
  });
  axios.post.mockResolvedValue({ status: 200, data: {} });
  axios.get.mockResolvedValue({ status: 200, data: [] });
});

const mockProps = {
  showHUDElements: true,
  pinnedTelemetry: [],
  isMetric: true,
  followDistance: 10,
  flightMode: 'Manual',
  isRecording: false
};

const mock_telemetry = {
  speed: 15,
  altitude: 1200,
  latitude: 37.7749,
  longitude: -122.4194,
  heading: 90,
  roll: -1.5,
  pitch: 0.6,
  yaw: 2.5
};

const test_main_container = () => {
  const container = document.getElementById('HUD');
  expect(container).toBeInTheDocument();
}

test('Disconnected Drone, Disconnected Server', async () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  render(<HUD {...mockProps} />);

  test_main_container();

  // Wait for the component to settle and show disconnected state (attempts to connect before showing disconnected)
  await waitFor(() => {
    expect(screen.getByText('Loading telemetry...')).toBeInTheDocument();
    expect(screen.getAllByText('Disconnected').length).toBeGreaterThan(0);
  }, { timeout: 2000 });

  // Test for ErrorIcon existence - drone is disconnected so error should be present
  expect(document.getElementById('drone-disconnected')).toBeInTheDocument();
  expect(screen.getByLabelText('Vehicle connection has been lost')).toBeInTheDocument();

  // Overlay should be red when drone is disconnected
  const overlay = document.getElementById('overlay');
  expect(overlay).toBeInTheDocument();
  expect(overlay?.className).toContain('bg-red-500/10');
  expect(overlay?.className).toContain('border-red-500/80');
});

test('Connected Drone, Connected Server', () => {
  useWebSocket.mockReturnValue({connectionStatus: 'connected', droneConnection: true, telemetryData: null});
  render(<HUD {...mockProps} />);
  test_main_container();

  expect(screen.getByText('Connected')).toBeInTheDocument();

  // Drone is connected, so ErrorIcon should not be present
  expect(document.getElementById('drone-disconnected')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Vehicle connection has been lost')).not.toBeInTheDocument();

  // Overlay should be neutral when drone is connected
  const overlay = document.getElementById('overlay');
  expect(overlay).toBeInTheDocument();
  expect(overlay?.className).toContain('bg-black/10');
  expect(overlay?.className).toContain('border-white/20');
});

// test('Ensure Telemetry Integrity', () => {
//   useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
//   render(<HUD {...mockProps} />);
// });

test('Pinned Telemetry in HUD Displays', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'connected', droneConnection: true, telemetryData: mock_telemetry});
  const telemetryProps = {
    ...mockProps,
    pinnedTelemetry: ['speed', 'altitude', 'latitude', 'longitude']
  };
  render(<HUD {...telemetryProps} />);
  test_main_container();

  // Test Pinned Telemetry Container exists and has correct number of items
  const pinnedTelemetryContainers = document.querySelectorAll('#pinned-telemetry');
  expect(pinnedTelemetryContainers.length).toBe(4);

  // Test that each pinned telemetry item is rendered
  const speedItem = document.getElementById('telemetry-icon-speed');
  const altitudeItem = document.getElementById('telemetry-icon-altitude');
  const latitudeItem = document.getElementById('telemetry-icon-latitude');
  const longitudeItem = document.getElementById('telemetry-icon-longitude');

  expect(speedItem).toBeInTheDocument();
  expect(altitudeItem).toBeInTheDocument();
  expect(latitudeItem).toBeInTheDocument();
  expect(longitudeItem).toBeInTheDocument();

  // Test that the telemetry values are displayed correctly (metric format)
  expect(speedItem?.nextSibling?.textContent).toContain(`${mock_telemetry.speed.toFixed(2)} m/s`);
  expect(altitudeItem?.nextSibling?.textContent).toContain(`${mock_telemetry.altitude.toFixed(2)} m`);
  expect(latitudeItem?.nextSibling?.textContent).toContain(`${mock_telemetry.latitude.toFixed(3)}°`);
  expect(longitudeItem?.nextSibling?.textContent).toContain(`${mock_telemetry.longitude.toFixed(3)}°`);
});

test('Check Follow Distance', () => {
  useWebSocket.mockReturnValue({ 
    connectionStatus: 'disconnected', 
    droneConnection: false, 
    telemetryData: null,
    trackingData: { tracking: true, tracked_class: 'person' }
  });
  render(<HUD {...mockProps} />);
  test_main_container();

  const distToTarget = document.getElementById('dist-to-target');
  expect(distToTarget).toBeInTheDocument();
});

test('Check Flight Mode', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  render(<HUD {...mockProps} />);
  test_main_container();
  
  const flightMode = document.getElementById('flight-mode');
  expect(flightMode).toBeInTheDocument();
  expect(flightMode?.textContent).toBe('Manual');
});

test('Start Recording', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  const props = {...mockProps, isRecording: true};
  render(<HUD {...props} />);
  test_main_container();
  expect(document.getElementById('recording')).toBeInTheDocument();
});

test('Stop Recording', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  const props = {...mockProps, isRecording: false};
  render(<HUD {...props} />);
  test_main_container();
  expect(document.getElementById('recording')).not.toBeInTheDocument();
});

test('Metric Units Display', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: mock_telemetry});
  const metricProps = {
    ...mockProps,
    pinnedTelemetry: ['speed', 'altitude', 'roll'],
    isMetric: true
  };
  render(<HUD {...metricProps} />);
  test_main_container();

  const speedItem = document.getElementById('telemetry-icon-speed');
  const altitudeItem = document.getElementById('telemetry-icon-altitude');
  const rollItem = document.getElementById('telemetry-icon-roll');

  expect(speedItem?.nextSibling?.textContent).toContain('m/s');
  expect(altitudeItem?.nextSibling?.textContent).toContain('m');
  expect(rollItem?.nextSibling?.textContent).toContain('°');
});

test('Imperial Units Display', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: mock_telemetry});
  const imperialProps = {
    ...mockProps,
    pinnedTelemetry: ['speed', 'altitude', 'roll'],
    isMetric: false
  };
  render(<HUD {...imperialProps} />);
  test_main_container();

  const speedItem = document.getElementById('telemetry-icon-speed');
  const altitudeItem = document.getElementById('telemetry-icon-altitude');
  const rollItem = document.getElementById('telemetry-icon-roll');

  expect(speedItem?.nextSibling?.textContent).toContain('ft/s');
  expect(altitudeItem?.nextSibling?.textContent).toContain('ft');
  expect(rollItem?.nextSibling?.textContent).toContain('°');
});

test('HUD Elements Toggle', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  const props = {...mockProps, showHUDElements: false};
  render(<HUD {...props} />);
  test_main_container();

  expect(document.getElementById('HUD-elements')).not.toBeInTheDocument();
  expect(document.getElementById('overlay')).not.toBeInTheDocument();
  expect(document.getElementById('HUD-telemetry')).not.toBeInTheDocument();
  expect(document.getElementById('HUD-flight-mode')).not.toBeInTheDocument();
  expect(document.getElementById('HUD-battery')).not.toBeInTheDocument();
});

test('Battery Gauge Display', () => {
  const battery_percent = 75.3657389;
  const battery_usage = 70.5754;
  const buildStylesSpy = jest.spyOn(cpb, 'buildStyles');  // Spy on buildStyles
  useWebSocket.mockReturnValue({batteryData: { percentage: battery_percent, usage: battery_usage }});
  render(<HUD {...mockProps} />);

  // Check the gauge text
  const battery = document.getElementById('HUD-battery');
  expect(battery).toBeInTheDocument();
  const guage = document.getElementById('battery-guage');
  expect(guage).toBeInTheDocument();
  const gaugeText = guage.querySelector('.CircularProgressbar-text');
  expect(gaugeText).toBeInTheDocument();

  // Check that buildStyles was called with correct pathColor
  expect(buildStylesSpy).toHaveBeenCalledWith(
    expect.objectContaining({
      pathColor: 'red',
      rotation: 0.75,
      strokeLinecap: 'round',
      trailColor: '#eee',
      textColor: 'white'
    })
  );
});

test('Video Feed Shows Stream Without Errors', async () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'connected', droneConnection: true, telemetryData: null});
  render(<HUD {...mockProps} />);
  
  const videoFeed = document.getElementById('video-feed');
  expect(videoFeed).toBeInTheDocument();
  
  // Check that the video feed container exists
  const videoContainer = videoFeed.querySelector('.relative.w-full.h-full');
  expect(videoContainer).toBeInTheDocument();
  
  // Check that error is not displayed when connected
  expect(screen.queryByText(/Failed to connect to video stream/i)).not.toBeInTheDocument();
});

test('Video Feed Shows Error When Stream Fails', async () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'failed', droneConnection: false, telemetryData: null});
  render(<HUD {...mockProps} />);
  
  const videoFeed = document.getElementById('video-feed');
  expect(videoFeed).toBeInTheDocument();

  // Wait for error state to update
  await waitFor(() => {
    // Check that error message is displayed
    expect(screen.getByText(/Failed to connect to video stream/i)).toBeInTheDocument();
  });
});