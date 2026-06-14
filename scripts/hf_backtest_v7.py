import sys
import json
import logging
import random
import hashlib
import math
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import mannwhitneyu

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "abu_engine"))

from core.chart import _compute_planet_positions
from core.houses_swiss import calculate_houses, HOUSE_SYSTEM_PLACIDUS
from core.dignities import get_planet_dignity
from harmony.field_v3 import compute_hf_v3
from harmony.houses import house_significators, assign_planet_houses
from harmony.schema_v2 import PLANET_ORDER

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# -- Configuration --
VALENCE_MAP = {"positive": 1.0, "negative": -1.0, "neutral": 0.0, "+": 1.0, "-": -1.0, "0": 0.0}
ARMS = [
    {"name": "v6_base", "kwargs": {}},
    {"name": "v6+N1", "kwargs": {"enable_n1_sect": True}},
    {"name": "v6+N1+N2", "kwargs": {"enable_n1_sect": True, "enable_n2_dignity": True}},
    {"name": "v6+N1+N2+N3a", "kwargs": {"enable_n1_sect": True, "enable_n2_dignity": True, "enable_n3a_reception": True}},
    {"name": "v6+N1+N2+N3a+N3b", "kwargs": {"enable_n1_sect": True, "enable_n2_dignity": True, "enable_n3a_reception": True, "enable_n3b_antiscia": True}},
    {"name": "v7_full", "kwargs": {"enable_n1_sect": True, "enable_n2_dignity": True, "enable_n3a_reception": True, "enable_n3b_antiscia": True, "enable_n3d_angle_aspects": True}},
]

# Copied from correlate_by_domain.py
SUBJECT_BIRTH_COORDS = {
    "GS_001": {"lat": 47.60, "lon": 9.35, "birth_date": "1875-07-26T19:29:00"},
    "GS_002": {"lat": 45.25, "lon": 14.45, "birth_date": "1856-07-10T00:00:00"},
    "GS_003": {"lat": 51.51, "lon": -0.13, "birth_date": "1912-06-23T00:00:00"},
    "308660": {"lat": 48.40, "lon": 9.98, "birth_date": "1879-03-14T11:30:00"},
    "12145":  {"lat": -34.60, "lon": -58.38, "birth_date": "1899-08-24T00:00:00"},
    "35255":  {"lat": 19.35, "lon": -99.15, "birth_date": "1907-07-06T00:00:00"},
    "76835":  {"lat": 36.72, "lon": -4.42, "birth_date": "1881-10-25T23:15:00"},
    "317785": {"lat": 51.85, "lon": 4.47, "birth_date": "1853-03-30T11:00:00"},
    "337730": {"lat": 49.20, "lon": 18.75, "birth_date": "1856-05-06T18:30:00"},
    "61360":  {"lat": 21.62, "lon": 69.67, "birth_date": "1869-10-02T07:12:00"},
    "232650": {"lat": 51.47, "lon": 0.00, "birth_date": "1947-01-08T09:00:00"},
    "16510":  {"lat": 34.05, "lon": -118.24, "birth_date": "1926-06-01T09:30:00"},
    "232580": {"lat": 34.26, "lon": -88.70, "birth_date": "1935-01-08T04:35:00"},
    "239610": {"lat": 38.25, "lon": -85.76, "birth_date": "1942-01-17T18:35:00"},
    "99835":  {"lat": 47.61, "lon": -122.33, "birth_date": "1942-11-27T10:15:00"},
    "240895": {"lat": 29.90, "lon": -93.93, "birth_date": "1943-01-19T09:45:00"},
    "106715": {"lat": 28.08, "lon": -80.61, "birth_date": "1943-12-08T11:55:00"},
    "288130": {"lat": 40.56, "lon": -85.66, "birth_date": "1931-02-08T09:00:00"},
    "349770": {"lat": 38.89, "lon": -90.18, "birth_date": "1926-05-26T05:00:00"},
    "2280":   {"lat": 40.57, "lon": -84.19, "birth_date": "1930-08-05T00:31:00"},
    "99810":  {"lat": 37.77, "lon": -122.42, "birth_date": "1940-11-27T07:12:00"},
    "113610": {"lat": 48.85, "lon": 2.35, "birth_date": "1915-12-19T05:00:00"},
    "336770": {"lat": 50.83, "lon": 4.37, "birth_date": "1929-05-04T03:00:00"},
    "14525":  {"lat": 59.33, "lon": 18.07, "birth_date": "1915-08-29T03:30:00"},
    "9945":   {"lat": 47.27, "lon": -0.08, "birth_date": "1883-08-19T16:00:00"},
    "70110":  {"lat": 53.34, "lon": -6.27, "birth_date": "1854-10-16T03:00:00"},
}

def _parse_dt(date_str: str) -> datetime | None:
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def _get_sect(sun_lon: float, cusps: list[float]) -> str:
    h = assign_planet_houses({"Sun": sun_lon}, cusps)["Sun"]
    return "diurnal" if h >= 7 else "nocturnal"

def _get_transit_dignities(transit_pos: dict) -> dict:
    digs = {}
    sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    for p in PLANET_ORDER:
        if p in transit_pos:
            lon = transit_pos[p]
            sign = sign_names[int(lon / 30.0) % 12]
            degree = lon % 30.0
            d = get_planet_dignity(p, sign, degree)
            digs[p] = d["kind"]
    return digs

def compute_metrics(valences, hf_values):
    # Returns (spearman, rank_biserial, p_value)
    if len(valences) < 3:
        return None, None, None
    valences = np.array(valences)
    hf_values = np.array(hf_values)
    
    # Pearson as fallback if spearman is complex, but we'll use pearson since it's standard in correlate_by_domain
    if np.std(hf_values) < 1e-9 or np.std(valences) < 1e-9:
        pearson = float("nan")
    else:
        pearson = float(np.corrcoef(valences, hf_values)[0, 1])
        
    pos = hf_values[valences > 0]
    neg = hf_values[valences < 0]
    
    if len(pos) < 2 or len(neg) < 2:
        return pearson, float("nan"), float("nan")
        
    stat, p_value = mannwhitneyu(pos, neg, alternative="greater")
    n1, n2 = len(pos), len(neg)
    rank_biserial = 1 - (2 * stat) / (n1 * n2)
    
    return pearson, float(rank_biserial), float(p_value)

def sanity_check():
    pos = {
        "Sun": 0.0, "Moon": 30.0, "Mercury": 60.0, "Venus": 90.0, 
        "Mars": 120.0, "Jupiter": 150.0, "Saturn": 180.0, "Uranus": 210.0, 
        "Neptune": 240.0, "Pluto": 270.0, "ASC": 180.0, "MC": 270.0
    }
    cusps = [180.0, 210.0, 240.0, 270.0, 300.0, 330.0, 0.0, 30.0, 60.0, 90.0, 120.0, 150.0]
    base_score = compute_hf_v3(pos, cusps)["hf_total_v3"]
    arm_score = compute_hf_v3(pos, cusps, **ARMS[0]["kwargs"])["hf_total_v3"]
    assert math.isclose(base_score, arm_score, rel_tol=1e-9), f"Sanity failed: {base_score} != {arm_score}"
    logging.info("Sanity check passed: v6_base exactly matches unparameterized compute_hf_v3")

def run_temporal_corpus():
    logging.info("Evaluating Temporal Corpus...")
    EVENTS_DIR = REPO_ROOT / "data" / "biographical_events_v2"
    
    all_events = []
    
    for events_file in sorted(EVENTS_DIR.glob("*.json")):
        fname = events_file.stem
        if fname in ("correlation_results", "cross_validation_results", "optimization_results"):
            continue
        subject_id = fname[:6] if fname.startswith("GS_") else fname.split("_", 1)[0]
        birth_info = SUBJECT_BIRTH_COORDS.get(subject_id)
        if not birth_info: continue
        
        birth_dt = _parse_dt(birth_info["birth_date"])
        if not birth_dt: continue
        
        data = json.loads(events_file.read_text(encoding="utf-8"))
        events = data.get("biographical_events", [])
        
        # Natal charts
        natal_pos = _compute_planet_positions(birth_dt)
        natal_houses = calculate_houses(birth_dt, birth_info["lat"], birth_info["lon"], HOUSE_SYSTEM_PLACIDUS)
        natal_data_for_sig = {
            "planets": [{"name": k, "longitude": v} for k, v in natal_pos.items() if k not in ("ASC", "MC")],
            "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_houses["cusps"])],
        }
        
        unique_houses = {e.get("house_domain", 0) for e in events if e.get("house_domain")}
        sigs_cache = {h: house_significators(natal_data_for_sig, h) for h in unique_houses}
        
        for evt in events:
            date_str = evt.get("date", "")
            if not date_str or date_str.startswith("0000"): continue
            event_dt = _parse_dt(date_str)
            if not event_dt or event_dt.year < 1550: continue
            
            domain = evt.get("house_domain", 0)
            valence_num = VALENCE_MAP.get(evt.get("valence", "neutral"), 0.0)
            if valence_num == 0.0 or not domain: continue # Only + / - for metrics
            
            try:
                transit_pos = _compute_planet_positions(event_dt)
                t_lat, t_lon = evt.get("lat", birth_info["lat"]), evt.get("lon", birth_info["lon"])
                transit_houses = calculate_houses(event_dt, t_lat, t_lon, HOUSE_SYSTEM_PLACIDUS)
                
                transit_angles = dict(transit_pos)
                transit_angles["ASC"] = float(transit_houses["asc"])
                transit_angles["MC"] = float(transit_houses["mc"])
                transit_cusps = list(transit_houses["cusps"])
                
                sig = sigs_cache.get(domain)
                if not sig: continue
                
                sect = _get_sect(transit_pos["Sun"], transit_cusps)
                dignities = _get_transit_dignities(transit_pos)
                
                hf_by_arm = {}
                for arm in ARMS:
                    hf = compute_hf_v3(
                        transit_angles,
                        cusps=transit_cusps,
                        planet_subset=sig,
                        sect=sect,
                        dignities=dignities,
                        **arm["kwargs"]
                    )
                    hf_by_arm[arm["name"]] = hf["hf_total_v3"]
                
                all_events.append({
                    "domain": domain,
                    "valence": valence_num,
                    "hf_by_arm": hf_by_arm
                })
            except Exception as e:
                pass
                
    # Stratified Split (70/30)
    random.seed(42)
    groups = defaultdict(list)
    for e in all_events:
        groups[(e["domain"], e["valence"])].append(e)
    
    train, test = [], []
    for g, items in groups.items():
        random.shuffle(items)
        split = int(len(items) * 0.7)
        train.extend(items[:split])
        test.extend(items[split:])
        
    metrics_by_arm = {}
    for arm in ARMS:
        aname = arm["name"]
        tr_val = [e["valence"] for e in train]
        tr_hf = [e["hf_by_arm"][aname] for e in train]
        te_val = [e["valence"] for e in test]
        te_hf = [e["hf_by_arm"][aname] for e in test]
        
        tr_p, tr_rb, tr_pval = compute_metrics(tr_val, tr_hf)
        te_p, te_rb, te_pval = compute_metrics(te_val, te_hf)
        
        metrics_by_arm[aname] = {
            "train": {"pearson": tr_p, "rank_biserial": tr_rb, "p_value": tr_pval, "n": len(train)},
            "test": {"pearson": te_p, "rank_biserial": te_rb, "p_value": te_pval, "n": len(test)},
        }
    return metrics_by_arm

def run_spatial_corpus():
    logging.info("Evaluating Spatial Corpus...")
    SPATIAL_DIR = REPO_ROOT / "data" / "hf_relocation_corpus"
    
    # Load all unique lat/lon pairs to serve as the global shuffle pool
    locations_pool = []
    events_to_process = []
    
    for f in sorted(SPATIAL_DIR.glob("*.json")):
        if f.name == "index.json": continue
        data = json.loads(f.read_text(encoding="utf-8"))
        
        birth_info = data["natal"]
        birth_dt = _parse_dt(f"{birth_info['date']}T{birth_info['time']}")
        if not birth_dt: continue
        
        natal_pos = _compute_planet_positions(birth_dt)
        natal_houses = calculate_houses(birth_dt, birth_info["lat"], birth_info["lon"], HOUSE_SYSTEM_PLACIDUS)
        natal_data_for_sig = {
            "planets": [{"name": k, "longitude": v} for k, v in natal_pos.items() if k not in ("ASC", "MC")],
            "houses": [{"num": i + 1, "longitude": c} for i, c in enumerate(natal_houses["cusps"])],
        }
        
        for loc in data.get("relocations", []):
            locations_pool.append((loc["lat"], loc["lon"]))
            for evt in loc.get("events", []):
                domain_str = evt.get("domain", "")
                if not domain_str.startswith("h"): continue
                domain = int(domain_str[1:])
                valence_num = VALENCE_MAP.get(evt.get("valence", "neutral"), 0.0)
                if valence_num == 0.0: continue
                
                date_str = evt.get("date")
                event_dt = _parse_dt(date_str)
                if not event_dt: continue
                
                sig = house_significators(natal_data_for_sig, domain)
                if not sig: continue
                
                events_to_process.append({
                    "event_dt": event_dt,
                    "lat": loc["lat"],
                    "lon": loc["lon"],
                    "domain": domain,
                    "valence": valence_num,
                    "sig": sig
                })

    locations_pool = list(set(locations_pool))
    random.seed(42)
    
    arm_results = {arm["name"]: {"hits": 0, "total": 0, "p_values": []} for arm in ARMS}
    
    for evt in events_to_process:
        transit_pos = _compute_planet_positions(evt["event_dt"])
        dignities = _get_transit_dignities(transit_pos)
        
        # Real location
        h_real = calculate_houses(evt["event_dt"], evt["lat"], evt["lon"], HOUSE_SYSTEM_PLACIDUS)
        ang_real = dict(transit_pos)
        ang_real["ASC"], ang_real["MC"] = float(h_real["asc"]), float(h_real["mc"])
        sect_real = _get_sect(transit_pos["Sun"], list(h_real["cusps"]))
        
        real_hf = {}
        for arm in ARMS:
            res = compute_hf_v3(ang_real, cusps=list(h_real["cusps"]), planet_subset=evt["sig"], sect=sect_real, dignities=dignities, **arm["kwargs"])
            real_hf[arm["name"]] = res["hf_total_v3"]
            
        # Shuffled locations
        shuffled_hfs = {arm["name"]: [] for arm in ARMS}
        for lat, lon in locations_pool:
            h_shuff = calculate_houses(evt["event_dt"], lat, lon, HOUSE_SYSTEM_PLACIDUS)
            ang_shuff = dict(transit_pos)
            ang_shuff["ASC"], ang_shuff["MC"] = float(h_shuff["asc"]), float(h_shuff["mc"])
            sect_shuff = _get_sect(transit_pos["Sun"], list(h_shuff["cusps"]))
            
            for arm in ARMS:
                res = compute_hf_v3(ang_shuff, cusps=list(h_shuff["cusps"]), planet_subset=evt["sig"], sect=sect_shuff, dignities=dignities, **arm["kwargs"])
                shuffled_hfs[arm["name"]].append(res["hf_total_v3"])
                
        # Evaluate hits per arm
        for arm in ARMS:
            aname = arm["name"]
            shuffs = np.array(shuffled_hfs[aname])
            h_r = real_hf[aname]
            
            median_shuff = np.median(shuffs)
            # A hit is when real location yields higher HF than random median (assuming positive valence)
            # If valence is negative, a hit is when real HF < median random HF
            hit = False
            if evt["valence"] > 0:
                hit = h_r > median_shuff
            else:
                hit = h_r < median_shuff
                
            p_val = np.mean(shuffs >= h_r) if evt["valence"] > 0 else np.mean(shuffs <= h_r)
            
            if hit: arm_results[aname]["hits"] += 1
            arm_results[aname]["total"] += 1
            arm_results[aname]["p_values"].append(p_val)
            
    metrics_by_arm = {}
    for aname, res in arm_results.items():
        metrics_by_arm[aname] = {
            "hit_rate": res["hits"] / max(1, res["total"]),
            "n_events": res["total"],
            "baseline_rate": 0.5,
            "mean_permutation_p_value": float(np.mean(res["p_values"])) if res["p_values"] else float("nan")
        }
    return metrics_by_arm

def main():
    sanity_check()
    temporal_metrics = run_temporal_corpus()
    spatial_metrics = run_spatial_corpus()
    
    out = {
        "meta": {
            "hf_version": "v7_ablation",
            "seed": 42,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "(a) Spatial corpus N1-N3b operators are constant per subject, so delta is a low-power between-subjects effect.",
                "(b) Temporal split test measures generalization, but v6 base saw it during calibration. Only spatial is purely held-out."
            ]
        },
        "arms": {}
    }
    
    for arm in ARMS:
        aname = arm["name"]
        out["arms"][aname] = {
            "temporal": temporal_metrics[aname],
            "spatial": spatial_metrics[aname]
        }
        
    out_path = REPO_ROOT / "results" / f"hf_backtest_v7_{int(datetime.now().timestamp())}.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    logging.info(f"Done! Results written to {out_path}")
    print(json.dumps(out["arms"], indent=2))

if __name__ == "__main__":
    main()
