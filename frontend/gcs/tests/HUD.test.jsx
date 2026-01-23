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
    isRecording: false,
    batteryData: null
  });
  axios.post.mockResolvedValue({ status: 200, data: {} });
  axios.get.mockResolvedValue({ status: 200, data: [] });
});

const mockProps = {
  showHUDElements: true,
  pinnedTelemetry: [],
  isMetric: true,
  followDistance: 10,
  flightMode: 'Manual'
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
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null});
  render(<HUD {...mockProps} />);
  test_main_container();

  const followDist = document.getElementById('follow-dist');
  const distToTarget = document.getElementById('dist-to-target');

  expect(followDist).toBeInTheDocument();
  expect(distToTarget).toBeInTheDocument();
  expect(followDist?.textContent).toContain('Follow: 10.00 m');
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
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null, isRecording: true});
  render(<HUD {...mockProps} />);
  test_main_container();
  expect(document.getElementById('recording')).toBeInTheDocument();
});

test('Stop Recording', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'disconnected', droneConnection: false, telemetryData: null, isRecording: false});
  render(<HUD {...mockProps} />);
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
  const videoImg = videoFeed.querySelector('img');
  expect(videoImg).toBeInTheDocument();
  
  // Simulate successful video load
  if (videoImg) {
    const loadEvent = new Event('load', { bubbles: true });
    videoImg.dispatchEvent(loadEvent);
  }

  // Wait for streaming state to update
  await waitFor(() => {
    // Check that no error message is displayed
    expect(screen.queryByText(/Stream error/i)).not.toBeInTheDocument();
  });
});

test('Video Feed Shows Error When Stream Fails', async () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'connected', droneConnection: true, telemetryData: null});
  render(<HUD {...mockProps} />);
  
  const videoFeed = document.getElementById('video-feed');
  expect(videoFeed).toBeInTheDocument();

  const videoImg = videoFeed.querySelector('img');
  expect(videoImg).toBeInTheDocument();

  // Simulate video error
  if (videoImg) {
    const errorEvent = new Event('error', { bubbles: true });
    videoImg.dispatchEvent(errorEvent);
  }

  // Wait for error state to update
  await waitFor(() => {
    // Check that error message is displayed
    expect(screen.getByText('Stream error. Is the Python server running?')).toBeInTheDocument();
  });
});

test('Video Feed Shows Loading State Initially', () => {
  useWebSocket.mockReturnValue({ connectionStatus: 'connected', droneConnection: true, telemetryData: null});
  render(<HUD {...mockProps} />);
  
  const videoFeed = document.getElementById('video-feed');
  expect(videoFeed).toBeInTheDocument();

  // Should show "Connecting to stream..." initially before video loads
  expect(screen.getByText('Connecting to stream...')).toBeInTheDocument();
  
  // Should show loading spinner
  const spinner = videoFeed.querySelector('.animate-spin');
  expect(spinner).toBeInTheDocument();
});