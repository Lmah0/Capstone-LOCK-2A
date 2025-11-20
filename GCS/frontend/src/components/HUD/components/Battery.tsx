"use client";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import Tooltip from '@mui/material/Tooltip';
import { useWebSocket } from "@/providers/WebSocketProvider";

export default function BatteryGauge() {
  const { batteryData } = useWebSocket();

  return (
    <Tooltip 
      title={`Battery Usage: ${batteryData?.usage || 0} mAh\nBattery Percentage: ${batteryData?.percentage || 0}%`}
      placement="left"
    >
      <div id='battery-guage' className="backdrop-blur-sm bg-black-400 border border-white/20 rounded-lg p-2 shadow-lg">
        <div style={{ width: 80, height: 40 }}>
          <CircularProgressbar
          value={batteryData?.usage || 0}
          maxValue={100}
          circleRatio={0.5}
          styles={buildStyles({
            rotation: 0.75,
            strokeLinecap: "round",
            trailColor: "#eee",
            pathColor: (batteryData?.usage || 0) > 70 ? "red" : (batteryData?.usage || 0) > 30 ? "orange" : "limegreen",
            textColor: "white",
          })}
          text={`${(batteryData?.percentage || 0).toFixed(1)}%`}
        />
        </div>
      </div>
    </Tooltip>
  );
}
