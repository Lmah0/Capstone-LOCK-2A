export interface TelemetryPoint {
  object_id?: number; // ID of the tracked object
  object_class?: string; // Class of the tracked object
  timestamp: string; // ISO timestamp string
  latitude: number;
  longitude: number;
  altitude: number; // meters
  speed: number; // m/s
  heading: number; // degrees (0-360)
}

export interface TrajectoryStats {
  averageSpeed: number; // m/s
  maxSpeed: number; // m/s
  totalDistance: number; // meters
  altitudeGain: number; // meters
  minAltitude: number; // meters
  maxAltitude: number; // meters
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
