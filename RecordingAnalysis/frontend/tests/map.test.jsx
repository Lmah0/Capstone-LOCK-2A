// Test file for MapComponent and its animation controls
import { render, screen, cleanup, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MapComponent } from '../src/components/map/MapComponent';

// -------------------- Mock setup --------------------
const mockMapInstance = {
  on: jest.fn((event, cb) => {
    if (event === 'load') {
      // Trigger load event immediately to simulate map loading
      setTimeout(cb, 0);
    }
  }),
  off: jest.fn(),
  remove: jest.fn(),
  addSource: jest.fn(),
  addLayer: jest.fn(),
  setTerrain: jest.fn(),
  easeTo: jest.fn(),
  fitBounds: jest.fn(),
  getSource: jest.fn(() => mockGeoJSONSource),
  setFeatureState: jest.fn(),
  queryRenderedFeatures: jest.fn(() => []),
  getCanvas: jest.fn(() => ({ style: {} })),
};
const mockMarkerInstance = { setLngLat: jest.fn().mockReturnThis(), addTo: jest.fn().mockReturnThis() };
const mockGeoJSONSource = { setData: jest.fn(), _data: { geometry: { coordinates: [] } } };
const mockLngLatBounds = { extend: jest.fn() };

jest.mock('mapbox-gl', () => ({
  __esModule: true,
  default: {
    Map: jest.fn(() => mockMapInstance),
    Marker: jest.fn(() => mockMarkerInstance),
    LngLatBounds: jest.fn(() => mockLngLatBounds),
    accessToken: '',
  },
}));

const mockAnimationControls = {
  runAnimation: jest.fn(),
  stopAnimation: jest.fn(),
  pauseAnimation: jest.fn(),
  resumeAnimation: jest.fn(),
  restartAnimation: jest.fn(),
  skipAnimation: jest.fn(),
  getAnimationStatus: jest.fn(() => ({ isRunning: false, isPaused: false, progress: 0 })),
};
jest.mock('../src/hooks/useMapAnimation', () => ({
  useMapAnimation: jest.fn(() => mockAnimationControls),
}));

process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN = 'mock-token';

const mockTelemetryData = [
  { timestamp: '2025-11-08T10:30:00Z', latitude: 37.7749, longitude: -122.4194, altitude: 100, speed: 5.5, objectClass: 'person'},
  { timestamp: '2025-11-08T10:30:30Z', latitude: 37.7750, longitude: -122.4195, altitude: 105, speed: 6.2, objectClass: 'person' },
  { timestamp: '2025-11-08T10:31:00Z', latitude: 37.7751, longitude: -122.4196, altitude: 110, speed: 7.1, objectClass: 'person' },
];

// -------------------- Helpers --------------------
const renderMap = (props = {}) => render(
  <MapComponent telemetryData={mockTelemetryData} isPlaying={false} restartTrigger={0} skipTrigger={0} {...props} />
);

// -------------------- Global setup --------------------
beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));
  global.cancelAnimationFrame = jest.fn();
});

afterAll(() => console.error.mockRestore());
beforeEach(jest.clearAllMocks);
afterEach(cleanup);

// -------------------- Tests --------------------
describe('MapComponent', () => {

  test('renders empty state', () => {
    render(<MapComponent telemetryData={[]} isPlaying={false} restartTrigger={0} skipTrigger={0} />);
    expect(screen.getByText('No trajectory data to display')).toBeInTheDocument();
  });

  test('initializes map with sources, layers, and terrain', async () => {
    renderMap();

    const expectedSources = ['mapbox-dem', 'route', 'route-points'];
    const expectedLayers = ['sky', 'route-line', 'route-points-layer'];

    await waitFor(() => {
      expectedSources.forEach(src => expect(mockMapInstance.addSource).toHaveBeenCalledWith(src, expect.any(Object)));
      expectedLayers.forEach(layer => expect(mockMapInstance.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: layer })));
      expect(mockMapInstance.setTerrain).toHaveBeenCalled();
      expect(mockMapInstance.on).toHaveBeenCalledWith('load', expect.any(Function));
    });
  });

  test('handles animation controls correctly', async () => {
    // Test runAnimation when isPlaying is true
    await act(async () => {
      renderMap({ isPlaying: true });
    });
    
    // Wait for map load and animation to start
    await waitFor(() => {
      expect(mockAnimationControls.runAnimation).toHaveBeenCalled();
    }, { timeout: 3000 });
    
    cleanup();
    jest.clearAllMocks();

    // Test pauseAnimation - set up animation status first, then render
    mockAnimationControls.getAnimationStatus.mockReturnValue({ isRunning: true, isPaused: false, progress: 0.5 });
    
    await act(async () => {
      const { rerender } = renderMap({ isPlaying: true });
      // Change to not playing to trigger pause
      rerender(<MapComponent telemetryData={mockTelemetryData} isPlaying={false} restartTrigger={0} skipTrigger={0} />);
    });
    
    await waitFor(() => {
      expect(mockAnimationControls.pauseAnimation).toHaveBeenCalled();
    }, { timeout: 3000 });

    cleanup();
    jest.clearAllMocks();

    // Test resumeAnimation - set up paused state first
    mockAnimationControls.getAnimationStatus.mockReturnValue({ isRunning: false, isPaused: true, progress: 0.5 });
    
    await act(async () => {
      const { rerender } = renderMap({ isPlaying: false });
      // Change to playing to trigger resume
      rerender(<MapComponent telemetryData={mockTelemetryData} isPlaying={true} restartTrigger={0} skipTrigger={0} />);
    });
    
    await waitFor(() => {
      expect(mockAnimationControls.resumeAnimation).toHaveBeenCalled();
    }, { timeout: 3000 });

    cleanup();
    jest.clearAllMocks();

    // Test restartAnimation
    await act(async () => {
      const { rerender } = renderMap({ restartTrigger: 0 });
      rerender(<MapComponent telemetryData={mockTelemetryData} isPlaying={false} restartTrigger={1} skipTrigger={0} />);
    });
    
    await waitFor(() => {
      expect(mockAnimationControls.restartAnimation).toHaveBeenCalled();
    }, { timeout: 3000 });

    cleanup();
    jest.clearAllMocks();

    // Test skipAnimation
    await act(async () => {
      const { rerender } = renderMap({ skipTrigger: 0 });
      rerender(<MapComponent telemetryData={mockTelemetryData} isPlaying={false} restartTrigger={0} skipTrigger={1} />);
    });
    
    await waitFor(() => {
      expect(mockAnimationControls.skipAnimation).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  test('cleans up map on unmount', () => {
    const { unmount } = renderMap();
    unmount();
    expect(mockAnimationControls.stopAnimation).toHaveBeenCalled();
    expect(mockMapInstance.remove).toHaveBeenCalled();
  });

});