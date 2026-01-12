import { TelemetryPoint, TrajectoryStats } from "@/utils/types";

/**
 * Calculates trajectory statistics from telemetry data points
 */
export const calculateTrajectoryStats = (telemetryData: TelemetryPoint[], objClass: string): TrajectoryStats => {
  if (telemetryData.length === 0) {
    return {
      averageSpeed: 0,
      maxSpeed: 0,
      totalDistance: 0,
      altitudeGain: 0,
      minAltitude: 0,
      maxAltitude: 0,
      missionDuration: 0,
      totalPoints: 0,
      startTime: "",
      endTime: "",
      objectClass: "Unknown"
    };
  }

  // Calculate mission duration and times
  const startTime = new Date(telemetryData[0].timestamp);
  const endTime = new Date(telemetryData[telemetryData.length - 1].timestamp);
  const missionDuration = (endTime.getTime() - startTime.getTime()) / 1000; // Duration in seconds

  // Calculate speed statistics
  const speeds = telemetryData.map(point => point.speed);
  const averageSpeed = speeds.reduce((sum, speed) => sum + speed, 0) / speeds.length;
  const maxSpeed = Math.max(...speeds);

  // Calculate altitude statistics
  const altitudes = telemetryData.map(point => point.altitude);
  const maxAltitude = Math.max(...altitudes);
  const minAltitude = Math.min(...altitudes);
  
  // Calculate altitude difference
  const altitudeGain = telemetryData[telemetryData.length - 1].altitude - telemetryData[0].altitude;

  // Calculate total distance using Haversine formula
  let totalDistance = 0;
  for (let i = 1; i < telemetryData.length; i++) {
    const prev = telemetryData[i - 1];
    const curr = telemetryData[i];
    totalDistance += haversineDistance(prev.latitude, prev.longitude, curr.latitude, curr.longitude);
  }

  return {
    averageSpeed: Number(averageSpeed.toFixed(1)),
    maxSpeed: Number(maxSpeed.toFixed(1)),
    totalDistance: Number((totalDistance * 1000).toFixed(1)), // Convert to meters
    altitudeGain: Number(altitudeGain.toFixed(1)),
    minAltitude: Number(minAltitude.toFixed(1)),
    maxAltitude: Number(maxAltitude.toFixed(1)),
    missionDuration: Number(missionDuration.toFixed(0)),
    totalPoints: telemetryData.length,
    startTime: telemetryData[0].timestamp,
    endTime: telemetryData[telemetryData.length - 1].timestamp,
    objectClass: objClass
  };
};

/**
 * Calculates the distance between two points using the Haversine formula
 */
const haversineDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Converts degrees to radians
 */
const toRad = (deg: number): number => {
  return deg * (Math.PI / 180);
};

/**
 * Formats mission duration from seconds to readable time
 */
export const formatMissionDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
};

/**
 * Formats speed with appropriate units
 */
export const formatSpeed = (speed: number): string => {
  return `${speed} m/s`;
};

/**
 * Formats altitude with appropriate units
 */
export const formatAltitude = (altitude: number): string => {
  return `${altitude} m`;
};

/**
 * Formats distance with appropriate units
 */
export const formatDistance = (distance: number): string => {
  if (distance >= 1000) {
    return `${(distance / 1000).toFixed(1)} km`;
  } else {
    return `${distance.toFixed(0)} m`;
  }
};
