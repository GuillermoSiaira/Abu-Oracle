import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from textwrap import shorten

ABU_URL = os.getenv("ABU_URL", "https://abu-engine-bbrsyawaca-uc.a.run.app")

def fetch_chart(date_iso: str, lat: float, lon: float):
    r = requests.get(f"{ABU_URL}/api/astro/chart", params={"date": date_iso, "lat": lat, "lon": lon})
    r.raise_for_status()
    return r.json()

def fetch_chart_detailed(date_iso: str, lat: float, lon: float):
    r = requests.get(f"{ABU_URL}/api/astro/chart-detailed", params={"date": date_iso, "lat": lat, "lon": lon})
    r.raise_for_status()
    return r.json()

def fetch_chart_extended(date_iso: str, lat: float, lon: float, include_transits: bool = False, include_solar_return: bool = False, solar_return_year: int | None = None, include_ranking: bool = False):
    params = {"date": date_iso, "lat": lat, "lon": lon}
    if include_transits:
        params["include_transits"] = "true"
    if include_solar_return:
        params["include_solar_return"] = "true"
    if solar_return_year:
        params["solar_return_year"] = solar_return_year
    if include_ranking:
        params["include_ranking"] = "true"
    r = requests.get(f"{ABU_URL}/api/astro/chart/extended", params=params)
    r.raise_for_status()
    return r.json()

def fetch_forecast(birth: str, lat: float, lon: float, days: int = 30):
    start = datetime.utcnow().date().isoformat() + "T00:00:00Z"
    end = (datetime.utcnow().date() + timedelta(days=days)).isoformat() + "T00:00:00Z"
    r = requests.get(f"{ABU_URL}/api/astro/forecast", params={
        "birthDate": birth,
        "lat": lat,
        "lon": lon,
        "start": start,
        "end": end,
        "step": "1d"
    })
    r.raise_for_status()
    return r.json()

def fetch_life_cycles(birth: str):
    r = requests.get(f"{ABU_URL}/api/astro/life-cycles", params={"birthDate": birth})
    r.raise_for_status()
    return r.json()

def fetch_solar_return(birth: str, lat: float, lon: float, year: int | None = None):
    params = {"birthDate": birth, "lat": lat, "lon": lon}
    if year:
        params["year"] = year
    r = requests.get(f"{ABU_URL}/api/astro/solar-return", params=params)
    r.raise_for_status()
    return r.json()

def fetch_profections(birth: str, asc_sign: str, current_date_iso: str | None = None):
    params = {"birthDate": birth, "ascSign": asc_sign}
    if current_date_iso:
        params["currentDate"] = current_date_iso
    r = requests.get(f"{ABU_URL}/api/astro/profections", params=params)
    r.raise_for_status()
    return r.json()

def fetch_fardars(birth: str, sun_lon: float, asc_lon: float, current_date_iso: str | None = None):
    params = {"birthDate": birth, "sunLon": sun_lon, "ascLon": asc_lon}
    if current_date_iso:
        params["currentDate"] = current_date_iso
    r = requests.get(f"{ABU_URL}/api/astro/fardars", params=params)
    r.raise_for_status()
    return r.json()

def fetch_lots_endpoint(sun_lon: float, moon_lon: float, asc_lon: float, venus_lon: float | None = None, mercury_lon: float | None = None, cusps: list[float] | None = None):
    params: dict[str, object] = {"sunLon": sun_lon, "moonLon": moon_lon, "ascLon": asc_lon}
    if venus_lon is not None:
        params["venusLon"] = venus_lon
    if mercury_lon is not None:
        params["mercuryLon"] = mercury_lon
    if cusps is not None:
        params["cusps"] = json.dumps(cusps)
    r = requests.get(f"{ABU_URL}/api/astro/lots", params=params)
    r.raise_for_status()
    return r.json()

def fetch_lunar_mansion(moon_lon: float):
    r = requests.get(f"{ABU_URL}/api/astro/lunar-mansions", params={"moonLon": moon_lon})
    r.raise_for_status()
    return r.json()

def fetch_fixed_stars(planets_list: list[dict]):
    params = {"planets": json.dumps(planets_list)}
    r = requests.get(f"{ABU_URL}/api/astro/fixed-stars", params=params)
    r.raise_for_status()
    return r.json()

def fetch_transits(natal_planets_list: list[dict], date_iso: str, lat: float, lon: float, major_only: bool = True):
    params = {
        "natalPlanets": json.dumps(natal_planets_list),
        "date": date_iso,
        "lat": lat,
        "lon": lon,
        "includeMajorOnly": str(major_only).lower(),
    }
    r = requests.get(f"{ABU_URL}/api/astro/transits", params=params)
    r.raise_for_status()
    return r.json()

def _extract_value(p: dict, *keys):
    for k in keys:
        if k in p and isinstance(p[k], (int, float)):
            return float(p[k])
    return None

def _derive_persian_inputs_from_chart_detailed(chart_detailed: dict):
    planets = chart_detailed.get("planets") or []
    # Map by name for quick lookup
    by_name = { (p.get("name") or ""): p for p in planets }
    sun = by_name.get("Sun", {})
    moon = by_name.get("Moon", {})
    venus = by_name.get("Venus", {})
    mercury = by_name.get("Mercury", {})

    def get_lon(planet_entry: dict):
        return _extract_value(planet_entry, "longitude", "lon")

    sun_lon = get_lon(sun) or 0.0
    moon_lon = get_lon(moon) or 0.0
    venus_lon = get_lon(venus)
    mercury_lon = get_lon(mercury)

    asc_str = (chart_detailed.get("asc") or chart_detailed.get("houses", {}).get("asc"))
    asc_sign = None
    if isinstance(asc_str, str) and asc_str.strip():
        asc_sign = asc_str.split(" ")[0]

    asc_lon = chart_detailed.get("asc_longitude") or chart_detailed.get("ascLong") or chart_detailed.get("ascLon")
    if asc_lon is None:
        # sometimes in houses dict
        asc_lon = chart_detailed.get("houses", {}).get("asc_longitude")

    # cusps list
    cusps = None
    houses = chart_detailed.get("houses")
    if isinstance(houses, dict) and isinstance(houses.get("houses"), list):
        cusps = [h.get("longitude") for h in houses["houses"] if isinstance(h.get("longitude"), (int, float))]
    elif isinstance(houses, list):
        cusps = [h.get("longitude") for h in houses if isinstance(h.get("longitude"), (int, float))]

    # planets list for fixed stars and transits
    planets_list = []
    for p in planets:
        lon_val = _extract_value(p, "longitude", "lon")
        if lon_val is None:
            continue
        name = p.get("name") or "?"
        planets_list.append({"name": name, "longitude": float(lon_val)})

    return {
        "sun_lon": float(sun_lon),
        "moon_lon": float(moon_lon),
        "venus_lon": float(venus_lon) if venus_lon is not None else None,
        "mercury_lon": float(mercury_lon) if mercury_lon is not None else None,
        "asc_sign": asc_sign,
        "asc_lon": float(asc_lon) if isinstance(asc_lon, (int, float)) else None,
        "cusps": cusps,
        "planets_list": planets_list,
    }

def main():
    parser = argparse.ArgumentParser(description="Interactive Abu CLI")
    parser.add_argument("--birth", required=True, help="Birth datetime ISO (e.g. 1978-07-05T21:15:00Z)")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--days", type=int, default=30, help="Forecast horizon in days")
    parser.add_argument("--life", action="store_true", help="Show life cycles")
    parser.add_argument("--solar", action="store_true", help="Show solar return for current year")
    parser.add_argument("--detailed", action="store_true", help="Fetch chart-detailed (dignities, PoF, nodes, houses)")
    parser.add_argument("--extended", action="store_true", help="Fetch unified chart/extended (ALL Persian techniques in one call)")
    parser.add_argument("--persian", action="store_true", help="Fetch Persian techniques separately (profections, fardars, lots, lunar mansion, fixed stars)")
    parser.add_argument("--transits", action="store_true", help="Include transits vs natal for now at current location/time")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")
    args = parser.parse_args()

    birth = args.birth
    lat = args.lat
    lon = args.lon

    try:
        print(f"[INFO] Abu CLI starting | ABU_URL={ABU_URL}")
        
        # Extended mode: single call for everything
        if args.extended:
            extended_data = fetch_chart_extended(
                birth, lat, lon,
                include_transits=args.transits,
                include_solar_return=args.solar,
                include_ranking=False
            )
            if args.json:
                print(json.dumps(extended_data, ensure_ascii=False, indent=2))
                return
            
            # Pretty print extended mode
            chart_ext = extended_data.get("chart", {})
            extended_block = extended_data.get("extended", {})
            
            print("\n=== Extended Chart (unified Persian bundle) ===")
            print(f"Datetime: {chart_ext.get('datetime')}")
            print(f"Location: {chart_ext.get('location')}")
            
            planets = chart_ext.get("planets", [])[:8]
            print(f"\nPlanets (first 8):")
            for p in planets:
                name = p.get("name", "?")
                lon_val = p.get("longitude", p.get("lon"))
                sign = p.get("sign")
                dignity = p.get("dignity", {})
                score = dignity.get("score", 0) if isinstance(dignity, dict) else 0
                print(f"  {name:<10} {sign:<12} lon={lon_val:.2f}° dignity_score={score}")
            
            print("\n=== Extended Block ===")
            if extended_block.get("profections"):
                prof = extended_block["profections"]
                if "error" not in prof:
                    print(f"Profections → year={prof.get('year')} sign={prof.get('profected_sign')} lord={prof.get('time_lord')}")
                else:
                    print(f"Profections → {prof.get('error')}")
            
            if extended_block.get("fardars"):
                fard = extended_block["fardars"]
                if "error" not in fard:
                    cur = fard.get("current", {})
                    print(f"Firdaria → diurnal={fard.get('is_diurnal')} current={cur.get('major')}/{cur.get('sub')}")
                else:
                    print(f"Firdaria → {fard.get('error')}")
            
            if extended_block.get("lunar_mansion"):
                lm = extended_block["lunar_mansion"]
                if "error" not in lm:
                    print(f"Lunar Mansion → #{lm.get('index')} {lm.get('name')} ({lm.get('nature')})")
                else:
                    print(f"Lunar Mansion → {lm.get('error')}")
            
            if extended_block.get("lots"):
                lots = extended_block["lots"]
                if isinstance(lots, list):
                    names = ", ".join([l.get("name") for l in lots[:6] if l.get("name")])
                    print(f"Lots → {len(lots)} calculated [{names}]")
                else:
                    print(f"Lots → {lots.get('error')}")
            
            if extended_block.get("fixed_stars"):
                fs = extended_block["fixed_stars"]
                if isinstance(fs, list):
                    top = ", ".join([f"{x.get('star')}~{x.get('planet')}({x.get('orb')}°)" for x in fs[:3]])
                    print(f"Fixed Stars → {len(fs)} contacts [{top}]")
                else:
                    print(f"Fixed Stars → {fs.get('error')}")
            
            return
        
        # Legacy modes
        chart = fetch_chart(birth, lat, lon)
        chart_detailed = fetch_chart_detailed(birth, lat, lon) if args.detailed or args.persian else None
        forecast = fetch_forecast(birth, lat, lon, days=args.days)
        life = fetch_life_cycles(birth) if args.life else None
        solar = fetch_solar_return(birth, lat, lon) if args.solar else None
        persian_block = None

        if args.persian:
            # Derive inputs from chart-detailed (fallback to base chart if needed)
            if chart_detailed is None:
                chart_detailed = fetch_chart_detailed(birth, lat, lon)
            d = _derive_persian_inputs_from_chart_detailed(chart_detailed)
            now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

            prof = None
            if d.get("asc_sign"):
                prof = fetch_profections(birth, d["asc_sign"], now_iso)

            fard = None
            if d.get("sun_lon") is not None and d.get("asc_lon") is not None:
                fard = fetch_fardars(birth, d["sun_lon"], d["asc_lon"], now_iso)

            lots = None
            if d.get("sun_lon") is not None and d.get("moon_lon") is not None and d.get("asc_lon") is not None:
                lots = fetch_lots_endpoint(d["sun_lon"], d["moon_lon"], d["asc_lon"], d.get("venus_lon"), d.get("mercury_lon"), d.get("cusps"))

            mansion = None
            if d.get("moon_lon") is not None:
                mansion = fetch_lunar_mansion(d["moon_lon"])

            fixed = None
            if d.get("planets_list"):
                fixed = fetch_fixed_stars(d["planets_list"])

            transit = None
            if args.transits and d.get("planets_list"):
                transit = fetch_transits(d["planets_list"], now_iso, lat, lon, True)

            persian_block = {
                "profections": prof,
                "fardars": fard,
                "lots": lots,
                "lunar_mansion": mansion,
                "fixed_stars": fixed,
                "transits": transit,
            }
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if args.json:
        out = {"chart": chart, "chart_detailed": chart_detailed, "forecast": forecast, "life_cycles": life, "solar_return": solar, "persian": persian_block}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print("\n=== Abu Chart (planets excerpt) ===")
    planets = chart.get("planets", [])[:8]
    for p in planets:
        try:
            name = p.get("name", "?")
            # API sometimes returns 'lon' instead of 'longitude'
            lon_val = p.get("longitude", p.get("lon"))
            lat_val = p.get("latitude")  # may be absent / None
            sign = p.get("sign")
            line = f"{name:<10}"
            if isinstance(lon_val, (int, float)):
                line += f" lon={lon_val:.2f}"
            elif lon_val is not None:
                line += f" lon={lon_val}"
            if isinstance(lat_val, (int, float)):
                line += f" lat={lat_val:.2f}"
            if sign:
                line += f" sign={sign}"
            print(line)
        except Exception as ex:
            print(f"[WARN] Could not format planet entry: {ex} -> raw={p}")

    print("\n=== Forecast peaks (first 5) ===")
    for pk in (forecast.get("peaks") or [])[:5]:
        print(f"{pk.get('date')}  {pk.get('label')}  score={pk.get('score')}")

    if life:
        print("\n=== Life cycles (first 5) ===")
        for ev in (life.get("events") or [])[:5]:
            print(f"{ev.get('cycle'):<25} {ev.get('planet'):<8} angle={ev.get('angle')} approx={ev.get('approx')}")

    if solar:
        print("\n=== Solar Return summary ===")
        print(f"Datetime: {solar.get('solar_return_datetime')}")
        ss = solar.get('score_summary', {})
        if ss:
            print("Scores:")
            for k,v in ss.items():
                print(f"  {k}: {v}")

    if chart_detailed:
        print("\n=== Chart Detailed (PoF, Nodes, Dignities excerpt) ===")
        ap = (chart_detailed.get("arabic_parts") or {}).get("part_of_fortune") or {}
        nn = (chart_detailed.get("lunar_nodes") or {}).get("north_node") or {}
        print(f"Part of Fortune: {ap.get('formatted') or ap.get('sign')} @ {ap.get('longitude')}")
        print(f"North Node: {nn.get('formatted') or nn.get('sign')} @ {nn.get('longitude')}")

    if persian_block:
        print("\n=== Persian Techniques ===")
        if persian_block.get("profections"):
            pr = persian_block["profections"]
            print(f"Profections → year={pr.get('year')} sign={pr.get('profected_sign')} lord={pr.get('time_lord')}")
        if persian_block.get("fardars"):
            fd = persian_block["fardars"]
            cur = (fd or {}).get("current") or {}
            print(f"Firdaria → diurnal={fd.get('is_diurnal')} current={cur.get('major')} / {cur.get('sub')}")
        if persian_block.get("lunar_mansion"):
            lm = persian_block["lunar_mansion"]
            print(f"Lunar Mansion → #{lm.get('index')} {lm.get('name')} ({lm.get('nature')})")
        if persian_block.get("lots"):
            lots_list = persian_block["lots"] or []
            names = ", ".join([l.get("name") for l in lots_list[:6] if l.get("name")])
            print(f"Lots → {len(lots_list)} calculated [{names}]")
        if persian_block.get("fixed_stars"):
            fs = persian_block["fixed_stars"] or []
            top = ", ".join([f"{x.get('star')}~{x.get('planet')}({x.get('orb')})" for x in fs[:6]])
            print(f"Fixed Stars → {len(fs)} contacts [{top}]")

if __name__ == "__main__":
    main()
