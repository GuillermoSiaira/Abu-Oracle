# Key Calculations for Abu (Persian Astrology)
**Purpose:** Document the computations that make Abu a **Persian (classical/medieval) astrology** app and their mapping to endpoints.

## 1) Dignities and Debilities (Essential)
- **Domicile, Exaltation, Detriment, Fall** by sign and degree (classical tables).  
- **Score** per planet according to essential dignity (configurable).  
- **JSON output:** `planet.dignity = { kind, score }`

## 2) Houses and Axes (ASC/MC)
- Calculation of **ASC/MC** and **houses** (Placidus/other), with `pyswisseph`.  
- Assignment of **house** to each planet and **lots**.  
- **Output:** `houses[1..12]`, `planet.house`

## 3) Aspects and Relationships
- Major aspects (0, 60, 90, 120, 180) and minor (30, 45, 135, 150, optional).  
- **Orbs by planet/aspect** and **application/separation**.  
- **Reception (mutual/unidirectional)** and **sect** (diurnal/nocturnal).  
- **Output:** `aspects[] = {a, b, type, orb, applying, reception}`

## 4) Solar Conditions (Optical)
- **Combustion** (< 8° from Sun), **under beams** (< 17°), **cazimi** (< 0°17').  
- **Output:** `planet.solar_condition = { state, distance_deg }`

## 5) Lots/Parts
- **Fortune (Pars Fortunae)**, **Spirit (Pars Spiritus)**, and secondary (Eros, Nemesis...).  
- Diurnal/nocturnal formulas (depends on sect).  
- **Output:** `lots = [{name, longitude, sign, degree, house}]`

## 6) Profections
- Annual advance of **Ascendant by sign** (and monthly optional).  
- Determination of **annual ruler**.  
- **Output:** `profections = { year, sign, lord }`

## 7) Firdaria (Fardars) & Hyleg
- **Major periods** and **subperiods** by planet (diurnal/nocturnal sect).  
- **Hyleg/Alcocoden** (lifespan): requires houses and traditional rules.  
- **Output:** `fardars = [{major, start, end, sub: [...] }]`

## 8) Solar Return (SR) and Relocation
- Exact moment of **Sun's return** to natal degree/minute.  
- Calculation of **relocated SR** by lat/lon/timezone.  
- **Comparison** with natal (axis changes, angularity).  
- **Output:** `solar_return = {datetime, asc, mc, houses, planets, notes}`

## 9) Lunar Mansions
- Division into **28 mansions** (~12°51') by lunar longitude.  
- Electoral and symbolic use.  
- **Output:** `lunar_mansion = { index, name, start, end, notes }`

## 10) Fixed Stars
- Catalog (magnitude, nature) and **orbs by magnitude**.  
- Conjunctions and basic parans.  
- **Output:** `fixed_stars[] = { star, mag, long, match, orb }`

---

## Proposed Endpoints (Summary)
- `GET /api/astro/chart`  
- `GET /api/astro/transits?date=...`  
- `GET /api/astro/solar-return?year=...&lat=...&lon=...`  
- `GET /api/astro/profections?year=...`  
- `GET /api/astro/fardars`  
- `GET /api/astro/lots`  
- `GET /api/astro/lunar-mansions`  
- `GET /api/astro/fixed-stars`  

---

## Recommended Response Schema (Fragment)
```json
{
  "asc": "Gemini 14°",
  "mc": "Aquarius 22°",
  "houses": [{"num":1,"cusp":"Gem 14°"}, ...],
  "planets": [
    {"name":"Sun","sign":"Gemini","deg":21.2,"house":1,
     "dignity":{"kind":"domicile","score":+5},
     "solar_condition":{"state":"under_beams","distance_deg":12.3}
    }
  ],
  "aspects":[{"a":"Sun","b":"Saturn","type":"square","orb":3.2,"applying":true,"reception":"mutual"}],
  "lots":[{"name":"Fortuna","sign":"Leo","deg":18.1,"house":3}],
  "profections":{"year":41,"sign":"Cancer","lord":"Moon"},
  "fardars":[{"major":"Venus","start":"2024-01-01","end":"2028-12-31","sub":[...]}],
  "lunar_mansion":{"index":11,"name":"Al Zubrah","start":...,"end":...},
  "fixed_stars":[{"star":"Regulus","mag":1.4,"long":"Leo 29°","match":true,"orb":0.8}]
}
```