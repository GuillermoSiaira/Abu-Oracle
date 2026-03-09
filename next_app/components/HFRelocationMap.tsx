"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { Map, Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

type RankingEntry = {
  city?: string;
  country?: string;
  lat?: number;
  lon?: number;
  city_lat?: number;
  city_lon?: number;
  hf_total_v3?: number;
  hf_total_v3_norm?: number;
};

type HFRelocationMapProps = {
  geojsonUrl: string;
  rankingUrl?: string;
  initialZoom?: number;
  className?: string;
};

type HFGeoJSON = GeoJSON.FeatureCollection & {
  properties?: {
    subject_id?: string | number;
    name?: string;
    natal_latitude?: number | null;
    natal_longitude?: number | null;
  };
};

function pickTopCities(entries: RankingEntry[], topK = 5) {
  const seen = new Set<string>();
  const out: { lat: number; lon: number; label: string }[] = [];
  for (const item of entries) {
    const lat = item.lat ?? item.city_lat;
    const lon = item.lon ?? item.city_lon;
    if (lat == null || lon == null) continue;
    const label = [item.city, item.country].filter(Boolean).join(", ") || "City";
    const key = label.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ lat, lon, label });
    if (out.length >= topK) break;
  }
  return out;
}

export function HFRelocationMap({ geojsonUrl, rankingUrl, initialZoom = 2, className }: HFRelocationMapProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstance = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [geojson, setGeojson] = useState<HFGeoJSON | null>(null);
  const [cities, setCities] = useState<{ lat: number; lon: number; label: string }[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load GeoJSON
  useEffect(() => {
    setError(null);
    fetch(geojsonUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`GeoJSON not found (${res.status})`);
        return res.json();
      })
      .then((data) => setGeojson(data as HFGeoJSON))
      .catch((err) => setError(err.message));
  }, [geojsonUrl]);

  // Load ranking
  useEffect(() => {
    if (!rankingUrl) {
      setCities([]);
      return;
    }
    fetch(rankingUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`Ranking not found (${res.status})`);
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setCities(pickTopCities(data, 5));
        } else {
          setCities([]);
        }
      })
      .catch(() => setCities([]));
  }, [rankingUrl]);

  // Initialize / update map
  useEffect(() => {
    if (!mapRef.current || !geojson) return;

    // Clean existing markers and map
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
    if (mapInstance.current) {
      mapInstance.current.remove();
      mapInstance.current = null;
    }

    const natalLat = geojson.properties?.natal_latitude ?? 0;
    const natalLon = geojson.properties?.natal_longitude ?? 0;
    const center: [number, number] = [natalLon || 0, natalLat || 0];

    const map = new maplibregl.Map({
      container: mapRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center,
      zoom: initialZoom,
      attributionControl: false,
    });
    mapInstance.current = map;

    map.on("load", () => {
      map.addSource("hf", {
        type: "geojson",
        data: geojson,
      });

      map.addLayer({
        id: "hf-heatmap",
        type: "heatmap",
        source: "hf",
        paint: {
          "heatmap-weight": ["interpolate", ["linear"], ["get", "delta_hf"], -6, 0, 0, 0.5, 6, 1],
          "heatmap-intensity": 1,
          "heatmap-radius": 18,
          "heatmap-opacity": 0.9,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0.0,
            "rgba(49,76,192,0)",
            0.25,
            "#3b4cc0",
            0.45,
            "#8c96c6",
            0.55,
            "#f7f7f7",
            0.70,
            "#f4a582",
            1.0,
            "#b2182b",
          ],
        },
      });

      // Add a faint circle layer for hover/legend if needed
      map.addLayer({
        id: "hf-points",
        type: "circle",
        source: "hf",
        paint: {
          "circle-radius": 2,
          "circle-color": ["interpolate", ["linear"], ["get", "delta_hf"], -6, "#313695", 0, "#f7f7f7", 6, "#a50026"],
          "circle-opacity": 0.6,
        },
      });

      // Natal marker
      if (natalLat && natalLon) {
        const el = document.createElement("div");
        el.style.width = "16px";
        el.style.height = "16px";
        el.style.background = "gold";
        el.style.clipPath = "path('M8 0 L10 6 L16 6 L11 10 L13 16 L8 12 L3 16 L5 10 L0 6 L6 6 Z')";
        el.style.border = "1px solid #333";
        el.title = "Natal";
        const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([natalLon, natalLat]).addTo(map);
        markersRef.current.push(marker);
      }

      // City markers (top-5)
      cities.forEach((c) => {
        const el = document.createElement("div");
        el.className = "hf-city-marker";
        el.style.width = "10px";
        el.style.height = "10px";
        el.style.background = "#e11d48";
        el.style.border = "1px solid white";
        el.style.borderRadius = "9999px";
        const marker = new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([c.lon, c.lat])
          .setPopup(new maplibregl.Popup({ offset: 12 }).setHTML(`<strong>${c.label}</strong>`))
          .addTo(map);
        markersRef.current.push(marker);
      });
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [geojson, cities, initialZoom]);

  return (
    <div className={className}>
      <div ref={mapRef} style={{ height: "70vh", width: "100%", borderRadius: "12px", overflow: "hidden" }} />
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {!error && !geojson && <p className="mt-2 text-sm text-gray-600">Loading map data…</p>}
    </div>
  );
}

export default HFRelocationMap;
