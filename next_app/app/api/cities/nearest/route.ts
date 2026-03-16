import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

// Cache en memoria — se carga una vez al primer request
let citiesCache: Array<{ lat: number; lon: number; city: string; country: string }> | null = null;

function loadCities() {
  if (citiesCache) return citiesCache;

  // Docker: process.cwd()=/app, volume en /app/data/external/
  // Dev:    process.cwd()=next_app/, CSV en ../data/external/
  const candidates = [
    path.join(process.cwd(), 'data', 'external', 'worldcities.csv'),
    path.join(process.cwd(), '..', 'data', 'external', 'worldcities.csv'),
  ];
  const filePath = candidates.find(p => fs.existsSync(p));
  if (!filePath) throw new Error(`worldcities.csv not found. Tried: ${candidates.join(', ')}`);
  const csv = fs.readFileSync(filePath, 'utf-8');
  const lines = csv.split('\n');

  // Skip header line (lat,lon,city,country)
  const result: Array<{ lat: number; lon: number; city: string; country: string }> = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const parts = line.split(',');
    if (parts.length < 4) continue;
    const lat = parseFloat(parts[0]);
    const lon = parseFloat(parts[1]);
    if (isNaN(lat) || isNaN(lon)) continue;
    // country is last element; city is everything in between
    const country = parts[parts.length - 1].trim();
    const city = parts.slice(2, parts.length - 1).join(',').trim();
    result.push({ lat, lon, city, country });
  }

  citiesCache = result;
  console.log(`[cities/nearest] Loaded ${result.length} cities into cache`);
  return citiesCache;
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const lat = parseFloat(searchParams.get('lat') ?? '');
  const lon = parseFloat(searchParams.get('lon') ?? '');

  if (isNaN(lat) || isNaN(lon)) {
    return NextResponse.json({ error: 'Invalid coordinates' }, { status: 400 });
  }

  try {
    const cities = loadCities()!;
    let nearest = cities[0];
    let minDist = Infinity;

    for (const city of cities) {
      const d = haversine(lat, lon, city.lat, city.lon);
      if (d < minDist) {
        minDist = d;
        nearest = city;
      }
    }

    return NextResponse.json({
      city: nearest.city,
      country: nearest.country,
      lat: nearest.lat,
      lon: nearest.lon,
      distance_km: Math.round(minDist),
    });
  } catch (err: any) {
    console.error('[cities/nearest]', err);
    return NextResponse.json({ error: 'Failed to load cities data' }, { status: 500 });
  }
}
