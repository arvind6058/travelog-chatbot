"use client";

import React, { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapLegend } from "./MapLegend";

export interface MarkerItem {
  id: string;
  lat: number;
  lng: number;
  title: string;
  subtitle?: string;
  type: "origin" | "destination" | "current" | "driver" | "hub";
  details?: Record<string, any>;
}

interface AdminTrackingMapProps {
  markers?: MarkerItem[];
  routePoints?: [number, number][];
  center?: [number, number];
  zoom?: number;
  isLocationAvailable?: boolean;
  isRouteAvailable?: boolean;
  followEnabled?: boolean;
}

/**
 * Escapes a value before it is interpolated into Leaflet popup HTML.
 *
 * `bindPopup` accepts an HTML string that Leaflet injects with innerHTML, so
 * any backend-provided string (location names, shipment/driver names, statuses,
 * tracking ids) would otherwise be executed as markup — a stored XSS sink.
 */
const escapeHtml = (value: unknown): string => {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
};

// Custom Leaflet Markers with Google Maps-style Pins and Icons
const createCustomIcon = (type: MarkerItem["type"]) => {
  let bgColor = "#6366f1"; // indigo default
  let symbol = "📦";

  if (type === "origin") {
    bgColor = "#10b981"; // emerald green
    symbol = "🟢";
  } else if (type === "destination") {
    bgColor = "#ef4444"; // red
    symbol = "🔴";
  } else if (type === "current") {
    bgColor = "#6366f1"; // indigo
    symbol = "📦";
  } else if (type === "driver") {
    bgColor = "#8b5cf6"; // purple
    symbol = "🚚";
  } else if (type === "hub") {
    bgColor = "#f59e0b"; // amber
    symbol = "🏢";
  }

  const html = `
    <div style="
      background-color: ${bgColor};
      width: 38px;
      height: 38px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 14px rgba(0,0,0,0.45);
      border: 2.5px solid #ffffff;
      color: #ffffff;
    ">
      <div style="transform: rotate(45deg); display: flex; align-items: center; justify-content: center; font-size: 16px;">
        ${symbol}
      </div>
    </div>
  `;

  return L.divIcon({
    className: "custom-leaflet-marker",
    html: html,
    iconSize: [38, 38],
    iconAnchor: [19, 38],
    popupAnchor: [0, -38],
  });
};

export const AdminTrackingMap: React.FC<AdminTrackingMapProps> = ({
  markers = [],
  routePoints = [],
  center = [20.5937, 78.9629],
  zoom = 5,
  isLocationAvailable = true,
  isRouteAvailable = true,
  followEnabled = true,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const mapsApiKey = process.env.NEXT_PUBLIC_MAPS_API_KEY || process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

      const map = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: false,
        attributionControl: false,
      });

      L.control.zoom({ position: "topright" }).addTo(map);

      let tileUrl = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";
      let tileOptions: L.TileLayerOptions = {
        maxZoom: 19,
        subdomains: "abcd",
      };

      if (mapsApiKey) {
        tileUrl = `https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${mapsApiKey}`;
      }

      L.tileLayer(tileUrl, tileOptions).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        layerGroupRef.current = null;
      }
    };
  }, []);

  // Update markers, route polylines and viewport bounds whenever data changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;

    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    const bounds: L.LatLngExpression[] = [];

    // Add Markers
    markers.forEach((m) => {
      if (typeof m.lat === "number" && typeof m.lng === "number" && !isNaN(m.lat) && !isNaN(m.lng)) {
        const icon = createCustomIcon(m.type);
        const marker = L.marker([m.lat, m.lng], { icon }).addTo(layerGroup);

        const popupContent = `
          <div style="font-family: system-ui, sans-serif; padding: 6px; color: #0f172a; min-width: 190px;">
            <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 3px; display: flex; align-items: center; gap: 6px;">
              <span>${escapeHtml(m.title)}</span>
            </div>
            ${m.subtitle ? `<div style="font-size: 11px; color: #475569; margin-bottom: 6px;">${escapeHtml(m.subtitle)}</div>` : ""}
            <div style="font-size: 10px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 5px; margin-top: 4px; line-height: 1.5;">
              <div><strong>Coords:</strong> ${escapeHtml(m.lat.toFixed(5))}, ${escapeHtml(m.lng.toFixed(5))}</div>
              ${m.details?.status ? `<div><strong>Status:</strong> ${escapeHtml(m.details.status)}</div>` : ""}
              ${m.details?.mode ? `<div><strong>Mode:</strong> ${escapeHtml(m.details.mode)}</div>` : ""}
              ${m.details?.last_updated ? `<div><strong>Updated:</strong> ${escapeHtml(new Date(m.details.last_updated).toLocaleTimeString())}</div>` : ""}
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);
        bounds.push([m.lat, m.lng]);
      }
    });

    // Add Route Polyline if available
    if (routePoints && routePoints.length >= 2) {
      L.polyline(routePoints, {
        color: "#6366f1",
        weight: 4,
        opacity: 0.85,
        dashArray: "8, 8",
        lineCap: "round",
      }).addTo(layerGroup);

      routePoints.forEach((pt) => bounds.push(pt));
    }

    // Auto-center / Follow logic
    if (followEnabled && bounds.length > 0) {
      const currentMarker = markers.find((m) => m.type === "current" || m.type === "driver");
      if (currentMarker) {
        map.panTo([currentMarker.lat, currentMarker.lng], { animate: true });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 11, { animate: true });
      } else {
        map.fitBounds(L.latLngBounds(bounds), { padding: [50, 50], maxZoom: 13, animate: true });
      }
    }
  }, [markers, routePoints, followEnabled]);

  return (
    <div className="relative w-full h-full min-h-[440px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950">
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Map Legend Overlay */}
      <MapLegend />

      {/* Overlays for Unavailable Coordinates or Route */}
      {(!isLocationAvailable || markers.length === 0) && (
        <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-md z-10 flex flex-col items-center justify-center p-6 text-center">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3 text-slate-400 text-xl shadow-lg">
            📍
          </div>
          <h4 className="text-sm font-bold text-white mb-1">Location Unavailable</h4>
          <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
            No verified geographical GPS coordinates stored for this entity. Stored location text remains visible in the tracking details panel.
          </p>
        </div>
      )}

      {!isRouteAvailable && isLocationAvailable && markers.length > 0 && routePoints.length === 0 && (
        <div className="absolute top-4 left-4 z-10 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-[11px] font-semibold text-slate-400 flex items-center space-x-1.5 shadow-lg backdrop-blur-md">
          <span>🗺️ Route Unavailable</span>
        </div>
      )}
    </div>
  );
};
