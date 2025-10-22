import SpeedIcon from "@mui/icons-material/Speed";
import FlightIcon from "@mui/icons-material/Flight";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import PublicIcon from "@mui/icons-material/Public";
import ExploreIcon from "@mui/icons-material/Explore";
import RotateRightIcon from "@mui/icons-material/RotateRight";
import { SvgIconComponent } from "@mui/icons-material";

export interface TelemetryData {
  speed: number;
  altitude: number;
  latitude: number;
  longitude: number;
  heading: number;
  roll: number;
  pitch: number;
  yaw: number;
}

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
  heading: {
    icon: ExploreIcon,
    label: "Heading",
    tooltip: "Current heading/orientation",
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
