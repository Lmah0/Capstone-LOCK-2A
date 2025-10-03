"use client";

import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import Tooltip from '@mui/material/Tooltip';

export default function BatteryGauge() {
  const batteryPercentage = 82; // EDIT TO READ FROM ACTUAL BATTERY PERCENTAGE
  const batteryUsage = 45; // EDIT TO READ FROM ACTUAL BATTERY USAGE LEVEL (0-100%)

  return (
    <Tooltip 
      title={`Battery Usage: ${batteryUsage} mAh\nBattery Percentage: ${batteryPercentage}%`}
      placement="left"
    >
      <div className="backdrop-blur-md bg-black/30 border border-white/20 rounded-lg p-2 shadow-lg">
        <div style={{ width: 80, height: 40 }}>
          <CircularProgressbar
          value={batteryUsage}
          maxValue={100}
          circleRatio={0.5}
          styles={buildStyles({
            rotation: 0.75,
            strokeLinecap: "round",
            trailColor: "#eee",
            pathColor: batteryUsage > 70 ? "red" : batteryUsage > 30 ? "orange" : "limegreen",
            textColor: "white",
          })}
          text={`${batteryPercentage}%`}
        />
        </div>
      </div>
    </Tooltip>
  );
}
