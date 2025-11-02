import { Coordinates, TelemetryPoint } from "@/utils/types";

/**
 * Calculate bearing between two coordinates
 */
export const calculateBearing = (from: Coordinates, to: Coordinates): number => {
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  return (Math.atan2(dx, dy) * 180) / Math.PI;
};

/**
 * Calculate position offset behind a point given bearing and distance
 */
export const offsetBehind = (
  point: Coordinates,
  bearing: number,
  distance = 0.002
): Coordinates => {
  const rad = (bearing * Math.PI) / 180;
  const lng = point[0] - Math.sin(rad) * distance;
  const lat = point[1] - Math.cos(rad) * distance;
  return [lng, lat];
};

/**
 * Interpolate between two coordinates
 */
export const interpolateCoordinates = (
  start: Coordinates,
  end: Coordinates,
  progress: number
): Coordinates => {
  const lng = start[0] + (end[0] - start[0]) * progress;
  const lat = start[1] + (end[1] - start[1]) * progress;
  return [lng, lat];
};

/**
 * Calculate distance between two coordinates (simple Euclidean)
 */
export const calculateDistance = (from: Coordinates, to: Coordinates): number => {
  return Math.sqrt(
    Math.pow(to[0] - from[0], 2) + Math.pow(to[1] - from[1], 2)
  );
};


// Convert telemetry data to coordinate format for map display
export const telemetryToCoordinates = (telemetryData: TelemetryPoint[]) => {
  return telemetryData.map(point => [point.longitude, point.latitude] as [number, number]);
};