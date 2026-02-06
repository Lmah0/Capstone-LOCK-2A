export interface TelemetryPoint {
  timestamp: string; // ISO timestamp string
  latitude: number;
  longitude: number;
  speed: number; // m/s
  heading: number; // degrees (0-360)
}

export interface TrajectoryStats {
  averageSpeed: number; // m/s
  maxSpeed: number; // m/s
  totalDistance: number; // meters
  missionDuration: number; // seconds
  totalPoints: number;
  startTime: string;
  endTime: string;
  objectClass: string; // Classified name of the tracked object
}

export interface popupData {
    telemetryPoint: TelemetryPoint;
    pointIndex: number;
}

export type Coordinates = [number, number];

export interface RoutePoint {
  type: "Feature";
  id?: string | number;
  geometry: {
    type: "Point";
    coordinates: Coordinates;
  };
  properties: {
    position: Coordinates;
    speed: string;
    timestamp?: number;
    pointIndex?: number;
    telemetryIndex?: number; // Index to reference telemetry data
  };
}

export interface MapConfig {
  center: Coordinates;
  zoom: number;
  pitch: number;
  bearing: number;
  style: string;
}

export interface AnimationConfig {
  stepsPerSegment: number;
  hotspotsInterval: number;
  cameraOffset: number;
  cameraDuration: number;
}

export interface TerrainConfig {
  source: string;
  exaggeration: number;
}

export interface SkyConfig {
  sunPosition: [number, number];
  sunIntensity: number;
}
