"use client";
import { Box, Paper, Typography, Tooltip } from "@mui/material";
import { formatUnits } from "../../../utils/unitConversions";
import { telemetryConfig, isValidTelemetryKey} from "../../../utils/telemetryConfig";
import { useWebSocket } from "@/providers/WebSocketProvider";

interface TelemetryDataProps {
  pinnedTelemetry: string[];
  isMetric: boolean;
}

export default function TelemetryData({ pinnedTelemetry, isMetric }: TelemetryDataProps) {
  const { telemetryData } = useWebSocket();

  if (!telemetryData) {
    return (
      <Paper
        elevation={3}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          p: 1.5,
          borderRadius: 4,
          backgroundColor: "rgba(0,0,0,0.6)",
          border: "1px solid rgba(255,255,255,0.3)", 
          color: "white",
          minWidth: 400,
          minHeight: 70,
        }}
      >
        <Typography variant="body2" sx={{ opacity: 0.7 }}>
          Loading telemetry...
        </Typography>
      </Paper>
    );
  }

  const displayedTelemetry = pinnedTelemetry
    .filter(key => isValidTelemetryKey(key))
    .slice(0, 4); // Limit to 4 items for space

  return (
    <Paper
      elevation={3}
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-around",
        p: 1.5,
        borderRadius: 4,
        backgroundColor: "rgba(0,0,0,0.6)",
        border: "1px solid rgba(255,255,255,0.3)", 
        color: "white",
        minWidth: 400,
        minHeight: 70,
      }}
    >
      {displayedTelemetry.map((key) => {
        const config = telemetryConfig[key];
        const IconComponent = config.icon;
        
        let displayValue: string;
        switch (key) {
          case 'speed':
            const speedFormatted = formatUnits.speed(telemetryData?.speed, isMetric);
            displayValue = `${speedFormatted.value} ${speedFormatted.unit}`;
            break;
          case 'altitude':
            const altitudeFormatted = formatUnits.altitude(telemetryData?.altitude, isMetric);
            displayValue = `${altitudeFormatted.value} ${altitudeFormatted.unit}`;
            break;
          case 'latitude':
            displayValue = formatUnits.degrees(telemetryData?.latitude);
            break;
          case 'longitude':
            displayValue = formatUnits.degrees(telemetryData?.longitude);
            break;
          case 'heading':
            displayValue = formatUnits.degrees(telemetryData?.heading);
            break;
          case 'roll':
            displayValue = formatUnits.degrees(telemetryData?.roll);
            break;
          case 'pitch':
            displayValue = formatUnits.degrees(telemetryData?.pitch);
            break;
          case 'yaw':
            displayValue = formatUnits.degrees(telemetryData?.yaw);
            break;
          default:
            displayValue = 'N/A';
        }
        
        return (
          <Tooltip key={key} title={config.tooltip} placement="top">
            <Box id='pinned-telemetry' display="flex" flexDirection="column" alignItems="center">
              <IconComponent fontSize="medium" id={`telemetry-icon-${key}`}
                sx={{ 
                  opacity: 0.7,
                  ...(config.iconStyle || {})
                }} 
              />
              <Typography variant="body2">{displayValue}</Typography>
            </Box>
          </Tooltip>
        );
      })}
    </Paper>
  );
}