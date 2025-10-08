"use client";
import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MapPopupContent } from "./MapPopupContent";
import { useMapAnimation } from "@/hooks/useMapAnimation";
import { calculateBearing, offsetBehind } from "@/utils/mapUtils";
import { DEFAULT_MAP_CONFIG, DEFAULT_ANIMATION_CONFIG, DEFAULT_TERRAIN_CONFIG, DEFAULT_SKY_CONFIG,MAPBOX_ACCESS_TOKEN } from "@/utils/constants";
import { TelemetryPoint, Coordinates } from "@/utils/types";

interface MapComponentProps {
  coordinates?: [number, number][];
  telemetryData?: TelemetryPoint[];
  isPlaying?: boolean;
  restartTrigger?: number;
  skipTrigger?: number;
  onPauseResume?: () => void;
  pathCoordinates?: Coordinates[];
  onAnimationStart?: () => void;
  onAnimationEnd?: () => void;
  className?: string;
}

mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN;

export const MapComponent: React.FC<MapComponentProps> = ({
  coordinates,
  telemetryData,
  isPlaying,
  restartTrigger,
  skipTrigger,
  onPauseResume,
  pathCoordinates = [
    [-74.5, 40],
    [-74.49, 40.01],
    [-74.48, 40.015],
    [-74.47, 40.02],
    [-74.465, 40.025],
    [-74.46, 40.03],
  ],
  onAnimationStart,
  onAnimationEnd,
  className = "",
}) => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const marker = useRef<mapboxgl.Marker | null>(null);
  const prevIsPlaying = useRef<boolean | undefined>(undefined);
  const lastRestartTrigger = useRef<number>(0);
  const lastSkipTrigger = useRef<number>(0);

  // State for popup data
  const [popupData, setPopupData] = useState<{
    coords: Coordinates;
    telemetryPoint?: TelemetryPoint;
    speed: string;
    timestamp?: number;
    pointIndex?: number;
  } | null>(null);
  const [selectedWaypointId, setSelectedWaypointId] = useState<string | number | null>(null);

  // Use coordinates prop if provided, otherwise fall back to pathCoordinates
  const finalCoordinates = coordinates || pathCoordinates;

  const {
    runAnimation, 
    stopAnimation, 
    pauseAnimation, 
    resumeAnimation, 
    restartAnimation,
    skipAnimation,
    getAnimationStatus 
  } = useMapAnimation({
    map,
    marker,
    pathCoordinates: finalCoordinates,
    telemetryData,
    config: DEFAULT_ANIMATION_CONFIG,
    onAnimationEnd,
  });

  const initializeMap = () => {
    if (!mapContainer.current || map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: DEFAULT_MAP_CONFIG.style,
      center: DEFAULT_MAP_CONFIG.center,
      zoom: DEFAULT_MAP_CONFIG.zoom,
      pitch: DEFAULT_MAP_CONFIG.pitch,
      bearing: DEFAULT_MAP_CONFIG.bearing,
      renderWorldCopies: false, 
      projection: 'globe' as any,
      minZoom: 3, 
      maxZoom: 30, 
    });

    map.current.on("load", () => {
      setupTerrain();
      setupSky();
      setupSources();
      setupLayers();
      setupMarker();
      setupEventHandlers();
      
      // Position camera at starting location first, then start animation
      if (isPlaying && finalCoordinates.length > 0) {
        positionCameraAtStart(() => {
          onAnimationStart?.();
          runAnimation();
        });
      }
    });
  };

  const setupTerrain = () => {
    if (!map.current) return;
    
    map.current.addSource("mapbox-dem", {
      type: "raster-dem",
      url: "mapbox://mapbox.mapbox-terrain-dem-v1",
      tileSize: 512,
      maxzoom: 14,
    });
    
    map.current.setTerrain({ 
      source: "mapbox-dem", 
      exaggeration: DEFAULT_TERRAIN_CONFIG.exaggeration 
    });
  };

  const setupSky = () => {
    if (!map.current) return;
    
    map.current.addLayer({
      id: "sky",
      type: "sky",
      paint: {
        "sky-type": "atmosphere",
        "sky-atmosphere-sun": DEFAULT_SKY_CONFIG.sunPosition,
        "sky-atmosphere-sun-intensity": DEFAULT_SKY_CONFIG.sunIntensity,
      },
    });
  };

  const setupSources = () => {
    if (!map.current) return;

    // Route line source
    map.current.addSource("route", {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: { type: "LineString", coordinates: [finalCoordinates[0]] },
        properties: {},
      },
    });

    // Route points source
    map.current.addSource("route-points", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  };

  const setupLayers = () => {
    if (!map.current) return;

    // Route line layer
    map.current.addLayer({
      id: "route-line",
      type: "line",
      source: "route",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": "#3b82f6", "line-width": 4 },
    });

    // Route points layer with hover and selected effects using expressions
    map.current.addLayer({
      id: "route-points-layer",
      type: "circle",
      source: "route-points",
      paint: { 
        "circle-radius": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          12, // selected size (largest)
          ["boolean", ["feature-state", "hover"], false],
          10, // hovered size
          8   // default size
        ],
        "circle-color": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          "#ef4444", // selected color (red)
          "#1d4ed8"  // default color (blue)
        ],
        "circle-stroke-width": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          4, // selected stroke width (thickest)
          ["boolean", ["feature-state", "hover"], false],
          3, // hovered stroke width
          2  // default stroke width
        ],
        "circle-stroke-color": "#ffffff",
      },
    });
  };

  const setupMarker = () => {
    if (!map.current) return;
    
    marker.current = new mapboxgl.Marker({ 
      color: "#ef4444",
      scale: 1.2,
    })
      .setLngLat(finalCoordinates[0])
      .addTo(map.current);
  };

  const positionCameraAtStart = (callback?: () => void) => {
    if (!map.current || finalCoordinates.length === 0) return;
    
    const startPosition = finalCoordinates[0];
    const endPosition = finalCoordinates[1] || startPosition;
    
    // Calculate initial bearing for camera positioning
    const bearing = finalCoordinates.length > 1 ? 
      calculateBearing(startPosition, endPosition) : 0;
    
    // Position camera behind the starting point
    const cameraPos = offsetBehind(startPosition, bearing, DEFAULT_ANIMATION_CONFIG.cameraOffset);
    
    // Move camera to starting position with animation
    map.current.easeTo({
      center: cameraPos,
      zoom: 16,
      pitch: 60,
      bearing,
      duration: 2000, // 2 second transition to starting position
      easing: (t) => 1 - Math.pow(1 - t, 3), // easeOutCubic for smooth transition
    });

    // Wait for camera movement to complete before starting animation
    if (callback) {
      setTimeout(callback, 1000); // Slightly longer than camera transition
    }
  };

  const setupEventHandlers = () => {
    if (!map.current) return;

    let hoveredFeatureId: string | number | null = null;
    let selectedFeatureId: string | number | null = null;

    map.current.on("click", "route-points-layer", (e) => {
      if (!e.features?.length) return;
      
      const feature = e.features[0];
      if (feature.geometry.type !== "Point") return;
      
      const coords = feature.geometry.coordinates as Coordinates;
      const { speed, timestamp, pointIndex, telemetryIndex } = feature.properties as { 
        speed: string; 
        timestamp?: number;
        pointIndex?: number;
        telemetryIndex?: number;
      };

      // Get the actual telemetry data using the stored index
      const telemetryPoint = telemetryData && telemetryIndex !== undefined ? telemetryData[telemetryIndex] : undefined;

      // Clear previous selection using React state
      if (selectedWaypointId !== null && selectedWaypointId !== undefined) {
        map.current!.setFeatureState(
          { source: "route-points", id: selectedWaypointId } as any,
          { selected: false }
        );
      }

      // Set new selection
      const newSelectedId = feature.id as string | number;
      setSelectedWaypointId(newSelectedId);
      selectedFeatureId = newSelectedId; // Keep local variable in sync
      if (newSelectedId !== undefined) {
        map.current!.setFeatureState(
          { source: "route-points", id: newSelectedId } as any,
          { selected: true }
        );
      }

      // Set popup data to show in overlay
      setPopupData({
        coords,
        telemetryPoint,
        speed,
        timestamp,
        pointIndex
      });
    });

    // Handle mouseenter for individual features
    map.current.on("mouseenter", "route-points-layer", (e) => {
      if (map.current && e.features && e.features.length > 0) {
        map.current.getCanvas().style.cursor = "pointer";
        
        // Remove hover state from previously hovered feature
        if (hoveredFeatureId !== null) {
          map.current.setFeatureState(
            { source: "route-points", id: hoveredFeatureId } as any,
            { hover: false }
          );
        }
        
        // Set hover state for current feature
        hoveredFeatureId = e.features[0].id as string | number;
        if (hoveredFeatureId !== undefined) {
          map.current.setFeatureState(
            { source: "route-points", id: hoveredFeatureId } as any,
            { hover: true }
          );
        }
      }
    });

    // Handle mouseleave
    map.current.on("mouseleave", "route-points-layer", () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = "";
        
        // Remove hover state from currently hovered feature
        if (hoveredFeatureId !== null) {
          map.current.setFeatureState(
            { source: "route-points", id: hoveredFeatureId } as any,
            { hover: false }
          );
          hoveredFeatureId = null;
        }
      }
    });

    // Handle general map clicks (close popup when clicking elsewhere)
    map.current.on("click", (e) => {
      // Check if the click was on a route point
      const features = map.current!.queryRenderedFeatures(e.point, {
        layers: ["route-points-layer"]
      });
      
      // If no route point was clicked, close the popup and clear selection
      if (features.length === 0) {
        setPopupData(null);
        // Clear selection using local variable (React state has stale closure issue)
        if (selectedFeatureId !== null && map.current) {
          map.current.setFeatureState(
            { source: "route-points", id: selectedFeatureId } as any,
            { selected: false }
          );
        }
        setSelectedWaypointId(null);
        selectedFeatureId = null; // Clear local variable
      }
    });
  };

  useEffect(() => {
    initializeMap();

    return () => {
      stopAnimation();
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Handle play/pause state changes
  useEffect(() => {
    if (!map.current || prevIsPlaying.current === isPlaying) return;
    
    prevIsPlaying.current = isPlaying;
    const status = getAnimationStatus();
    
    if (isPlaying) {
      if (status.isPaused) {
        resumeAnimation();
      } else if (!status.isRunning) {
        positionCameraAtStart(() => {
          runAnimation();
        });
      }
    } else {
      if (status.isRunning && !status.isPaused) {
        pauseAnimation();
      }
    }
  }, [isPlaying]);

  // Handle restart trigger changes
  useEffect(() => {
    if (restartTrigger && restartTrigger > 0 && restartTrigger !== lastRestartTrigger.current && map.current) {
      lastRestartTrigger.current = restartTrigger;
      restartAnimation();
    }
  }, [restartTrigger, restartAnimation]);

  // Handle skip trigger changes
  useEffect(() => {
    if (skipTrigger && skipTrigger > 0 && skipTrigger !== lastSkipTrigger.current && map.current) {
      lastSkipTrigger.current = skipTrigger;
      skipAnimation();
    }
  }, [skipTrigger, skipAnimation]);

  // Expose animation controls
  useEffect(() => {
    (window as any).mapAnimationControls = {
      restart: restartAnimation,
      stop: stopAnimation,
      pause: pauseAnimation,
      resume: resumeAnimation,
      getStatus: getAnimationStatus,
    };
  }, [restartAnimation, stopAnimation, pauseAnimation, resumeAnimation, getAnimationStatus]);

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainer} className={`h-full w-full ${className}`} />
      
      {/* Popup overlay positioned at top-left of map */}
      {popupData && (
        <div className="absolute top-4 left-4 z-[1000] max-w-80 drop-shadow-lg">
          <div className="relative">
            <button
              onClick={() => {
                setPopupData(null);
                // Clear selection when popup is closed
                if (selectedWaypointId !== null && selectedWaypointId !== undefined && map.current) {
                  map.current.setFeatureState(
                    { source: "route-points", id: selectedWaypointId } as any,
                    { selected: false }
                  );
                }
                setSelectedWaypointId(null);
              }}
              className="absolute top-2 right-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-white text-sm font-bold hover:bg-black/70 hover:scale-110 transition-all duration-200"
            >
              ×
            </button>
            <MapPopupContent 
              coords={popupData.coords} 
              telemetryPoint={popupData.telemetryPoint}
              speed={popupData.speed} 
              timestamp={popupData.timestamp}
              pointIndex={popupData.pointIndex}
            />
          </div>
        </div>
      )}
    </div>
  );
};
