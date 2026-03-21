"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
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
  distance_km?: number;
};

type CityInfo = {
  lat: number;
  lon: number;
  label: string;
  hf: number;
  delta: number;
  distance_km: number;
};

type Region = "all" | "europe" | "americas" | "asia" | "africa" | "oceania";

const REGION_BOUNDS: Record<Exclude<Region, "all">, [number, number, number, number]> = {
  europe:   [-25, 35, 45, 72],
  americas: [-170, -56, -30, 72],
  asia:     [25, -10, 180, 72],
  africa:   [-20, -36, 55, 38],
  oceania:  [100, -50, 180, 0],
};

const REGION_LABELS: Record<Region, string> = {
  all: "🌍 Global",
  europe: "🇪🇺 Europa",
  americas: "🌎 Américas",
  asia: "🌏 Asia",
  africa: "🌍 África",
  oceania: "🌏 Oceanía",
};

export type Domain = "global" | "h1" | "h2" | "h4" | "h5" | "h6" | "h7" | "h9" | "h10";

const DOMAIN_LABELS: Record<Domain, string> = {
  global: "Global",
  h1:     "Identidad",
  h2:     "Recursos",
  h4:     "Hogar",
  h5:     "Creatividad",
  h6:     "Trabajo",
  h7:     "Relaciones",
  h9:     "Expansión",
  h10:    "Carrera",
};

type MapClickData = { lat: number; lon: number; hfScore: number; deltaScore: number };

type HFRelocationMapProps = {
  geojsonUrl: string;
  rankingUrl?: string;
  natalHf?: number;
  initialZoom?: number;
  className?: string;
  mapHeight?: string;
  showLegend?: boolean;
  legendLow?: string;
  legendHigh?: string;
  /** Active house domain — reads hf_{domain}/delta_{domain} from multi-domain GeoJSON */
  domain?: Domain;
  /** Called when user clicks a point on the heatmap */
  onMapClick?: (data: MapClickData) => void;
};

type DomainScale = { p5: number; p95: number };

type HFGeoJSON = GeoJSON.FeatureCollection & {
  properties?: {
    subject_id?: string | number;
    name?: string;
    natal_latitude?: number | null;
    natal_longitude?: number | null;
  };
  domain_scales?: Record<string, DomainScale>;
};

/** Compute Top-K grid points from GeoJSON features for a given domain. */
function pickTopFromGeoJSON(features: GeoJSON.Feature[], domain: Domain, topK = 5): CityInfo[] {
  const hfKey   = `hf_${domain}`;
  const deltaKey = `delta_${domain}`;

  const sorted = [...features]
    .filter(f => f.properties?.[hfKey] != null)
    .sort((a, b) => (b.properties![hfKey] as number) - (a.properties![hfKey] as number));

  const out: CityInfo[] = [];
  for (const f of sorted) {
    if (out.length >= topK) break;
    const [lon, lat] = (f.geometry as GeoJSON.Point).coordinates;
    // Deduplicate: skip if within ~12° of an already-picked point
    if (out.some(s => Math.abs(s.lat - lat) < 12 && Math.abs(s.lon - lon) < 12)) continue;
    const hf    = f.properties![hfKey]    as number;
    const delta = (f.properties![deltaKey] as number) ?? 0;
    const latStr = `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? "N" : "S"}`;
    const lonStr = `${Math.abs(lon).toFixed(1)}°${lon >= 0 ? "E" : "W"}`;
    out.push({ lat, lon, label: `${latStr}, ${lonStr}`, hf, delta, distance_km: 0 });
  }
  return out;
}

function pickTopCities(entries: RankingEntry[], topK = 5): CityInfo[] {
  const seen = new Set<string>();
  const out: CityInfo[] = [];
  for (const item of entries) {
    const lat = item.lat ?? item.city_lat;
    const lon = item.lon ?? item.city_lon;
    if (lat == null || lon == null) continue;
    const label = [item.city, item.country].filter(Boolean).join(", ") || "City";
    const key = label.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ lat, lon, label, hf: item.hf_total_v3 ?? 0, delta: 0, distance_km: item.distance_km ?? 0 });
    if (out.length >= topK) break;
  }
  return out;
}

export function HFRelocationMap({ geojsonUrl, rankingUrl, natalHf, initialZoom = 2, className, mapHeight = "70vh", showLegend = true, legendLow = "Bajo", legendHigh = "Alto", domain, onMapClick }: HFRelocationMapProps) {
  // Ref para evitar closure stale en el useEffect del mapa
  const onMapClickRef = useRef(onMapClick);
  useEffect(() => { onMapClickRef.current = onMapClick; }, [onMapClick]);
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstance = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [geojson, setGeojson] = useState<HFGeoJSON | null>(null);
  const [cities, setCities] = useState<CityInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [region, setRegion] = useState<Region>("all");

  // Resolved property keys depending on domain mode
  const deltaKey = domain ? `delta_${domain}` : "delta_hf";
  const hfKey    = domain ? `hf_${domain}`    : "hf_total";

  // Color scale: p5→cold, p50→neutral, p95→hot — median-anchored for symmetric visual distribution
  const colorScale = useMemo<{ low: number; mid: number; high: number }>(() => {
    if (geojson?.features?.length) {
      const vals = geojson.features
        .map(f => f.properties?.[deltaKey] as number | undefined)
        .filter((v): v is number => v != null && isFinite(v));
      if (vals.length > 10) {
        vals.sort((a, b) => a - b);
        const n   = vals.length;
        const p5  = vals[Math.floor(n * 0.05)] ?? vals[0];
        const p50 = vals[Math.floor(n * 0.50)] ?? vals[Math.floor(n / 2)];
        const p95 = vals[Math.floor(n * 0.95)] ?? vals[n - 1];
        if (p95 > p5) return { low: p5, mid: p50, high: p95 };
      }
    }
    return { low: -6, mid: 0, high: 6 };
  }, [geojson, deltaKey]);

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

  // Filtered GeoJSON by region
  const filteredGeojson = useMemo(() => {
    if (!geojson || region === "all") return geojson;
    const bounds = REGION_BOUNDS[region];
    return {
      ...geojson,
      features: geojson.features.filter((f) => {
        const coords = (f.geometry as GeoJSON.Point).coordinates;
        const [lon, lat] = coords;
        return lon >= bounds[0] && lat >= bounds[1] && lon <= bounds[2] && lat <= bounds[3];
      }),
    } as HFGeoJSON;
  }, [geojson, region]);

  // Convert point grid → polygon cells so fill layer covers all zoom levels without gaps
  const gridGeojson = useMemo(() => {
    if (!filteredGeojson) return null;
    const HALF = 2.5; // half of 5° cell
    return {
      ...filteredGeojson,
      features: filteredGeojson.features.map(f => {
        const [lon, lat] = (f.geometry as GeoJSON.Point).coordinates;
        return {
          ...f,
          geometry: {
            type: "Polygon" as const,
            coordinates: [[
              [lon - HALF, lat - HALF],
              [lon + HALF, lat - HALF],
              [lon + HALF, lat + HALF],
              [lon - HALF, lat + HALF],
              [lon - HALF, lat - HALF],
            ]],
          },
        };
      }),
    } as unknown as HFGeoJSON;
  }, [filteredGeojson]);

  // Top cities: from GeoJSON in domain mode, from rankingUrl in global mode
  const displayCities = useMemo<CityInfo[]>(() => {
    if (domain && filteredGeojson?.features?.length) {
      return pickTopFromGeoJSON(filteredGeojson.features, domain, 5);
    }
    return cities;
  }, [domain, filteredGeojson, cities]);

  // Initialize / update map
  useEffect(() => {
    if (!mapRef.current || !filteredGeojson) return;

    // Clean existing markers and map
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
    if (mapInstance.current) {
      mapInstance.current.remove();
      mapInstance.current = null;
    }

    const natalLat = filteredGeojson.properties?.natal_latitude ?? 0;
    const natalLon = filteredGeojson.properties?.natal_longitude ?? 0;
    const center: [number, number] = [natalLon || 0, natalLat || 0];

    const map = new maplibregl.Map({
      container: mapRef.current,
      scrollZoom: true,
      dragPan: true,
      style: {
        version: 8,
        sources: {
          // Base without labels — heatmap renders on top, then labels layer over both
          "carto-base": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
              "https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
              "https://c.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
          },
        },
        layers: [
          { id: "carto-base-layer", type: "raster", source: "carto-base", minzoom: 0, maxzoom: 19 },
        ],
      },
      center,
      zoom: initialZoom,
      attributionControl: false,
    });
    mapInstance.current = map;

    map.on("load", () => {
      map.addSource("hf", {
        type: "geojson",
        data: filteredGeojson,
      });

      const { low, mid, high } = colorScale;

      // heatmap weight anchored at median for symmetric visual distribution

      // heatmap-weight: p5→0, p50→0.5, p95→1
      const weightStops: unknown[] = [
        "interpolate", ["linear"], ["get", deltaKey],
        low, 0,
        mid, 0.5,
        high, 1,
      ];

      // Heatmap: radius tuned so kernels don't oversaturate at low zoom
      map.addLayer({
        id: "hf-heat",
        type: "heatmap",
        source: "hf",
        paint: {
          "heatmap-weight":    weightStops as maplibregl.ExpressionSpecification,
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 0.7, 3, 1.2, 5, 1.8, 7, 2.5],
          "heatmap-radius":    ["interpolate", ["linear"], ["zoom"], 0, 10, 2, 15, 3, 24, 4, 42, 5, 75],
          "heatmap-color": [
            "interpolate", ["linear"], ["heatmap-density"],
            0,    "rgba(0,0,0,0)",
            0.05, "rgba(30,27,75,0.55)",
            0.25, "rgba(67,56,128,0.68)",
            0.50, "rgba(107,101,117,0.75)",
            0.75, "rgba(196,124,47,0.85)",
            0.90, "rgba(217,149,50,0.92)",
            1.0,  "rgba(220,38,80,0.97)",
          ],
          "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 0, 0.78, 4, 0.70, 7, 0.55],
        },
      });

      // Invisible circle layer — only for hover/tooltip interaction
      map.addLayer({
        id: "hf-hover",
        type: "circle",
        source: "hf",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 6, 3, 10, 5, 18],
          "circle-color":   "rgba(0,0,0,0)",
          "circle-opacity": 0,
        },
      });

      // Labels tile on top of heatmap — green-tinted (Matrix style)
      map.addSource("carto-labels", {
        type: "raster",
        tiles: [
          "https://a.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}@2x.png",
          "https://b.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}@2x.png",
          "https://c.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}@2x.png",
        ],
        tileSize: 256,
      });
      map.addLayer({
        id: "carto-labels-layer",
        type: "raster",
        source: "carto-labels",
        paint: {
          "raster-opacity":    0.90,
          "raster-hue-rotate": 115,
          "raster-saturation": 0.6,
          "raster-brightness-min": 0.05,
        },
      });


      // Natal marker with popup
      if (natalLat && natalLon) {
        const el = document.createElement("div");
        el.style.width = "16px";
        el.style.height = "16px";
        el.style.background = "gold";
        el.style.clipPath = "path('M8 0 L10 6 L16 6 L11 10 L13 16 L8 12 L3 16 L5 10 L0 6 L6 6 Z')";
        el.style.border = "1px solid #333";
        el.style.cursor = "pointer";
        el.title = "Natal";
        const hfLabel = natalHf != null ? natalHf.toFixed(2) : "—";
        const popup = new maplibregl.Popup({ offset: 12, closeButton: false })
          .setHTML(`<div style="font-family:monospace;font-size:12px;color:#111;padding:2px 0"><strong>★ Natal</strong><br/>HF: ${hfLabel}<br/>${natalLat.toFixed(2)}°, ${natalLon.toFixed(2)}°</div>`);
        const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([natalLon, natalLat]).setPopup(popup).addTo(map);
        markersRef.current.push(marker);
      }

      // City markers (top-5) with rich popups
      displayCities.forEach((c, i) => {
        const el = document.createElement("div");
        el.style.position = "relative";
        el.style.width = "22px";
        el.style.height = "22px";
        el.style.background = "#e11d48";
        el.style.border = "2px solid white";
        el.style.borderRadius = "9999px";
        el.style.display = "flex";
        el.style.alignItems = "center";
        el.style.justifyContent = "center";
        el.style.color = "white";
        el.style.fontSize = "11px";
        el.style.fontWeight = "700";
        el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.5)";
        el.style.cursor = "pointer";
        el.textContent = String(i + 1);
        const delta = natalHf != null ? (c.hf - natalHf) : 0;
        const deltaSign = delta >= 0 ? "+" : "";
        const deltaColor = delta >= 0 ? "#16a34a" : "#dc2626";
        const popupHtml = `<div style="font-family:monospace;font-size:12px;color:#111;padding:2px 0;min-width:140px">
          <strong>#${i + 1} ${c.label}</strong><br/>
          HF: ${c.hf.toFixed(2)}
          <span style="color:${deltaColor};font-weight:700"> (${deltaSign}${delta.toFixed(2)})</span><br/>
          📍 ${c.lat.toFixed(1)}°, ${c.lon.toFixed(1)}°<br/>
          📏 ${Math.round(c.distance_km).toLocaleString()} km
        </div>`;
        const marker = new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([c.lon, c.lat])
          .setPopup(new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(popupHtml))
          .addTo(map);
        markersRef.current.push(marker);
      });
      // Hover tooltip via invisible circle layer
      const tooltip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: "hf-tooltip" });
      map.on("mouseenter", "hf-hover", () => { map.getCanvas().style.cursor = "crosshair"; });
      map.on("mouseleave", "hf-hover", () => { map.getCanvas().style.cursor = ""; tooltip.remove(); });
      map.on("mousemove", "hf-hover", (e) => {
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties;
        if (!props) return;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;
        const delta = (props[deltaKey] ?? props.delta_hf ?? 0) as number;
        const hfVal = (props[hfKey] ?? props.hf_total ?? 0) as number;
        const sign = delta >= 0 ? "+" : "";
        const color = delta >= 0 ? "#d99532" : "#78508c";
        tooltip
          .setLngLat([coords[0], coords[1]])
          .setHTML(`<div style="font-family:monospace;font-size:11px;color:#e2e8f0;background:#1e1b2e;padding:4px 8px;border-radius:6px;border:1px solid #334155">
            HF: ${Number(hfVal).toFixed(2)} <span style="color:${color};font-weight:700">(${sign}${Number(delta).toFixed(2)})</span><br/>
            ${Number(coords[1]).toFixed(1)}°, ${Number(coords[0]).toFixed(1)}°
          </div>`)
          .addTo(map);
      });

      // Click handler — registrado aquí dentro de 'load' garantiza que 'hf-hover' existe
      // map.remove() en cleanup elimina todos los listeners automáticamente
      map.on('click', 'hf-hover', (e: maplibregl.MapLayerMouseEvent) => {
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties;
        if (!props) return;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;
        const hfScore = (props[hfKey] ?? props.hf_total ?? 0) as number;
        const deltaScore = (props[deltaKey] ?? props.delta_hf ?? 0) as number;
        onMapClickRef.current?.({ lat: coords[1], lon: coords[0], hfScore, deltaScore });
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
  }, [filteredGeojson, displayCities, domain, deltaKey, hfKey, colorScale, initialZoom, natalHf]);

  // Handle region change: fly to bounds
  const handleRegionChange = (r: Region) => {
    setRegion(r);
    if (r !== "all" && mapInstance.current) {
      const [minLon, minLat, maxLon, maxLat] = REGION_BOUNDS[r];
      mapInstance.current.fitBounds([[minLon, minLat], [maxLon, maxLat]], { padding: 30, duration: 800 });
    } else if (r === "all" && mapInstance.current) {
      const natalLat = geojson?.properties?.natal_latitude ?? 0;
      const natalLon = geojson?.properties?.natal_longitude ?? 0;
      mapInstance.current.flyTo({ center: [natalLon || 0, natalLat || 0], zoom: initialZoom, duration: 800 });
    }
  };

  return (
    <div className={className}>
      <div style={{ position: "relative" }}>
        <div ref={mapRef} style={{ height: mapHeight, width: "100%", borderRadius: "12px", overflow: "hidden", touchAction: "none" }} />

        {/* Region filter — top right */}
        {geojson && (
          <div style={{
            position: "absolute", top: "12px", right: "12px", zIndex: 10,
          }}>
            <select
              value={region}
              onChange={(e) => handleRegionChange(e.target.value as Region)}
              style={{
                background: "rgba(10,10,20,0.85)", color: "#e2e8f0", border: "1px solid rgba(100,100,120,0.3)",
                borderRadius: "8px", padding: "6px 10px", fontSize: "12px", fontWeight: 600,
                backdropFilter: "blur(4px)", cursor: "pointer", outline: "none",
              }}
            >
              {(Object.keys(REGION_LABELS) as Region[]).map((r) => (
                <option key={r} value={r}>{REGION_LABELS[r]}</option>
              ))}
            </select>
          </div>
        )}

        {/* Mini-ranking panel — top left */}
        {displayCities.length > 0 && (
          <div style={{
            position: "absolute", top: "12px", left: "12px", zIndex: 10,
            background: "rgba(10,10,20,0.85)", borderRadius: "8px", padding: "8px 12px",
            backdropFilter: "blur(4px)", border: "1px solid rgba(100,100,120,0.3)",
            minWidth: "180px",
          }}>
            <span style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>
              {domain ? `Top 3 · ${DOMAIN_LABELS[domain]}` : "Top 3"}
            </span>
            {displayCities.slice(0, 3).map((c, i) => {
              // Domain mode: use pre-computed delta_hX from GeoJSON (correct scale)
              // Global mode: compute against natalHf
              const delta = domain ? c.delta : (natalHf != null ? c.hf - natalHf : 0);
              const sign = delta >= 0 ? "+" : "";
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px", fontSize: "11px" }}>
                  <span style={{
                    width: "18px", height: "18px", borderRadius: "9999px", background: "#e11d48",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "white", fontSize: "10px", fontWeight: 700, flexShrink: 0,
                  }}>{i + 1}</span>
                  <span style={{ color: "#e2e8f0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "120px" }}>
                    {c.label}
                  </span>
                  <span style={{ color: delta >= 0 ? "#d99532" : "#78508c", fontWeight: 700, fontFamily: "monospace", marginLeft: "auto" }}>
                    {sign}{delta.toFixed(1)}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Color scale legend */}
        {showLegend && geojson && (
          <div
            style={{
              position: "absolute",
              bottom: "16px",
              right: "16px",
              background: "rgba(10, 10, 20, 0.85)",
              borderRadius: "8px",
              padding: "8px 12px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              backdropFilter: "blur(4px)",
              border: "1px solid rgba(100,100,120,0.3)",
              zIndex: 10,
            }}
          >
            <span style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 600, letterSpacing: "0.05em" }}>
              Harmony Field (Δ)
            </span>
            <div
              style={{
                width: "140px",
                height: "12px",
                borderRadius: "4px",
                background: "linear-gradient(to right, #1e1b4b, #433880, #78508c, #6b6575, #b4643c, #d99532, #dc2650)",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "#94a3b8" }}>
              <span>{legendLow}</span>
              <span>{legendHigh}</span>
            </div>
          </div>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {!error && !geojson && <p className="mt-2 text-sm text-gray-600">Loading map data…</p>}
    </div>
  );
}

export default HFRelocationMap;
