// Test file for MissionStats and ControlPanel components in the dashboard
import { render, screen, cleanup, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import MissionStats from '../src/components/MissionStats';
import {ControlPanel} from '../src/components/ui/ControlPanel';

// Silence console errors during test runs
beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterAll(() => {
  console.error.mockRestore();
});

beforeEach(jest.clearAllMocks);
afterEach(cleanup);

describe('MissionStats Component', () => {
    const mockTrajectoryStats = {
        averageSpeed: 15.5, // m/s
        maxSpeed: 25.8, // m/s
        totalDistance: 2450.0, // meters
        altitudeGain: 120.5, // meters
        minAltitude: 98.2, // meters
        maxAltitude: 218.7, // meters
        missionDuration: 420, // seconds (7 minutes)
        totalPoints: 94,
        startTime: '2025-11-08T10:30:00Z',
        endTime: '2025-11-08T10:37:00Z',
        objectClass: 'person'
    };

    const expectMainContainer = () => {
        const container = document.getElementById('mission-stats');
        expect(container).toBeInTheDocument();
    };

    test('renders all mission statistics correctly', () => {
        render(<MissionStats trajectoryStats={mockTrajectoryStats} />);
        expectMainContainer();

        // Verify all labels
        const labels = [
        'Object Class',
        'Mission Duration',
        'Average Speed',
        'Max Speed',
        'Total Distance',
        'Altitude Gain',
        'Max Altitude',
        'Min Altitude',
        ];

        labels.forEach(label => expect(screen.getByText(label)).toBeInTheDocument());

        // Verify formatted values
        expect(screen.getByText('person')).toBeInTheDocument();
        expect(screen.getByText('7m 0s')).toBeInTheDocument(); // missionDuration
        expect(screen.getByText('15.5 m/s')).toBeInTheDocument(); // averageSpeed
        expect(screen.getByText('25.8 m/s')).toBeInTheDocument(); // maxSpeed
        expect(screen.getByText('2.5 km')).toBeInTheDocument(); // totalDistance (formatted)
        expect(screen.getByText('120.5 m')).toBeInTheDocument(); // altitudeGain
        expect(screen.getByText('218.7 m')).toBeInTheDocument(); // maxAltitude
        expect(screen.getByText('98.2 m')).toBeInTheDocument(); // minAltitude
    });

    test('renders loading state when trajectoryStats is null', () => {
        render(<MissionStats trajectoryStats={null} />);
        expect(screen.getByText('Loading statistics...')).toBeInTheDocument();
    });

});

describe('Mission Control', () => {
    const props = {
        onReplayMission: jest.fn(),
        onPauseResume: jest.fn(),
        onSkip: jest.fn(),
        isPlaying: false,
        isCompleted: false
    };
    const expectMainContainer = () => {
        const container = document.getElementById('control-panel');
        expect(container).toBeInTheDocument();
    };

   test('Controls on Animation not Complete, not Playing', () => {
    const { container } = render(<ControlPanel {...props} />);
    expectMainContainer();
    const panel = within(container); // Scope queries to this component

    expect(panel.getByText('Mission Control')).toBeInTheDocument();
    expect(panel.getByText('Restart Mission')).toBeInTheDocument();
    expect(panel.getByText('Resume')).toBeInTheDocument();

    // Verify buttons
    expect(panel.getByRole('button', { name: /restart mission/i })).toBeInTheDocument();
    expect(panel.getByRole('button', { name: /resume/i })).toBeInTheDocument();
  });

  test('Controls on Animation not Complete, Playing', () => {
    const { container } = render(<ControlPanel {...props} isPlaying={true} />);
    expectMainContainer();
    const panel = within(container);

    expect(panel.getByText('Mission Control')).toBeInTheDocument();
    expect(panel.getByText('Restart Mission')).toBeInTheDocument();
    expect(panel.getByText('Pause')).toBeInTheDocument();

    // Verify buttons
    expect(panel.getByRole('button', { name: /restart mission/i })).toBeInTheDocument();
    expect(panel.getByRole('button', { name: /pause/i })).toBeInTheDocument();
  });

  test('Controls on Animation Completed', () => {
    const { container } = render(<ControlPanel {...props} isCompleted={true} />);
    expectMainContainer();
    const panel = within(container);

    expect(panel.getByText('Mission Control')).toBeInTheDocument();
    expect(panel.getByText('Restart Mission')).toBeInTheDocument();

    // Verify buttons
    expect(panel.getByRole('button', { name: /restart mission/i })).toBeInTheDocument();
    expect(panel.queryByRole('button', { name: /Replay/i })).toBeInTheDocument();
  });
});