"use client";

import { Box, Paper, Typography, Tooltip } from "@mui/material";
import SpeedIcon from "@mui/icons-material/Speed"; // speedometer icon
import FlightIcon from "@mui/icons-material/Flight"; // for altitude
import LocationOnIcon from "@mui/icons-material/LocationOn"; // for latitude
import PublicIcon from "@mui/icons-material/Public"; // for longitude

export default function TelemetryData() {
  return (
    <Paper
      elevation={3}
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-around",
        p: 2,
        borderRadius: 4,
        backgroundColor: "rgba(0,0,0,0.6)", // more transparent background
        color: "white",
        minWidth: 400,
      }}
    >
      {/* Speed */}
      <Tooltip title="Current speed of the vehicle" placement="top">
        <Box display="flex" flexDirection="column" alignItems="center">
          <SpeedIcon fontSize="large" sx={{ opacity: 0.7 }} />
          <Typography variant="body1">23 kph</Typography>
        </Box>
      </Tooltip>

      {/* Altitude */}
      <Tooltip title="Current altitude above sea level" placement="top">
        <Box display="flex" flexDirection="column" alignItems="center">
          <FlightIcon fontSize="large" sx={{ opacity: 0.7 }} />
          <Typography variant="body1">86 m</Typography>
        </Box>
      </Tooltip>

      {/* Latitude */}
      <Tooltip title="Current latitude position" placement="top">
        <Box display="flex" flexDirection="column" alignItems="center">
          <LocationOnIcon fontSize="large" sx={{ opacity: 0.7 }} />
          <Typography variant="body1">40.7128°</Typography>
        </Box>
      </Tooltip>

      {/* Longitude */}
      <Tooltip title="Current longitude position" placement="top">
        <Box display="flex" flexDirection="column" alignItems="center">
          <PublicIcon fontSize="large" sx={{ opacity: 0.7 }} />
          <Typography variant="body1">-74.0060°</Typography>
        </Box>
      </Tooltip>
    </Paper>
  );
}
