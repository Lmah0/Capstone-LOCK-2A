import SpeedIcon from "@mui/icons-material/Speed";
import FlightIcon from "@mui/icons-material/Flight";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import PublicIcon from "@mui/icons-material/Public";
import ExploreIcon from "@mui/icons-material/Explore";
import RotateRightIcon from "@mui/icons-material/RotateRight";
import { SvgIconComponent } from "@mui/icons-material";

// Mock telemetry data (in base units - meters/second, meters, degrees)
export const telemetryData = {
    speed: 12.5, // m/s
    altitude: 150, // meters
    latitude: 40.712800, // degrees
    longitude: -74.006000, // degrees
    bearing: 245.0, // degrees
    roll: -2.1, // degrees
    pitch: 1.3, // degrees
    yaw: 245.7, // degrees
  }; 

export interface TelemetryItem {
  icon: SvgIconComponent;
  label: string;
  tooltip: string;
  color?: string;
  iconStyle?: React.CSSProperties;
}

export const telemetryConfig: Record<string, TelemetryItem> = {
  speed: {
    icon: SpeedIcon,
    label: "Ground Speed",
    tooltip: "Current speed of the vehicle",
    color: "#3b82f6"
  },
  altitude: {
    icon: FlightIcon,
    label: "Altitude",
    tooltip: "Current altitude above sea level",
    color: "#10b981"
  },
  latitude: {
    icon: LocationOnIcon,
    label: "Latitude",
    tooltip: "Current latitude position",
    color: "#f59e0b"
  },
  longitude: {
    icon: PublicIcon,
    label: "Longitude",
    tooltip: "Current longitude position",
    color: "#f56f50"
  },
  bearing: {
    icon: ExploreIcon,
    label: "Bearing",
    tooltip: "Current bearing/orientation",
    color: "#8b5cf6"
  },
  roll: {
    icon: RotateRightIcon,
    label: "Roll",
    tooltip: "Roll angle",
    color: "#ef4444"
  },
  pitch: {
    icon: RotateRightIcon,
    label: "Pitch",
    tooltip: "Pitch angle",
    color: "#06b6d4",
    iconStyle: { transform: 'rotate(90deg)' }
  },
  yaw: {
    icon: RotateRightIcon,
    label: "Yaw",
    tooltip: "Yaw angle",
    color: "#84cc16",
    iconStyle: { transform: 'rotate(45deg)' }
  }
};

// Helper function to get telemetry keys in a consistent order
export const getTelemetryKeys = (): string[] => {
  return Object.keys(telemetryConfig);
};

// Helper function to check if a telemetry key is valid
export const isValidTelemetryKey = (key: string): key is keyof typeof telemetryConfig => {
  return key in telemetryConfig;
};
