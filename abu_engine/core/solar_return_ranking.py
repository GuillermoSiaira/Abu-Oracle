# -*- coding: utf-8 -*-
"""
Solar Return Ranking Module (Persian/Hellenistic Astrology)

Scores Solar Return charts for multiple geographic locations using classical criteria:
- Essential dignities (domicile, exaltation, exile, fall)
- Angularity (planets in angular houses)
- Solar conditions (cazimi, under beams, combustion)
- Aspects with mutual reception
- Sect (diurnal/nocturnal affinity)

Author: AI Oracle Team
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from core.chart import solar_return_chart
from core.dignities import get_planet_dignity, get_ruler
from core.houses_swiss import calculate_houses, longitude_to_sign_degree, get_planet_house, HOUSE_SYSTEM_PLACIDUS


# Persian/Hellenistic scoring tables
DIGNITY_SCORES = {
    'domicile': 5,
    'exaltation': 4,
    'triplicity': 3,
    'term': 2,
    'face': 1,
    'peregrine': 0,
    'detriment': -4,
    'fall': -5
}

# Benefic and malefic classifications
BENEFICS = ['Jupiter', 'Venus']
MALEFICS = ['Saturn', 'Mars']
NEUTRALS = ['Sun', 'Moon', 'Mercury']

# City database for SR relocation (16 cities across elements/regions)
RELOCATION_CITIES = {
    # Fire cities (energetic, entrepreneurial)
    "Dubai": {"lat": 25.2048, "lon": 55.2708, "region": "Middle East"},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437, "region": "North America"},
    "Barcelona": {"lat": 41.3851, "lon": 2.1734, "region": "Europe"},
    "Sydney": {"lat": -33.8688, "lon": 151.2093, "region": "Oceania"},
    
    # Earth cities (stable, practical)
    "Zurich": {"lat": 47.3769, "lon": 8.5417, "region": "Europe"},
    "Singapore": {"lat": 1.3521, "lon": 103.8198, "region": "Asia"},
    "Toronto": {"lat": 43.6532, "lon": -79.3832, "region": "North America"},
    "Copenhagen": {"lat": 55.6761, "lon": 12.5683, "region": "Europe"},
    
    # Air cities (intellectual, communicative)
    "London": {"lat": 51.5074, "lon": -0.1278, "region": "Europe"},
    "Amsterdam": {"lat": 52.3676, "lon": 4.9041, "region": "Europe"},
    "San Francisco": {"lat": 37.7749, "lon": -122.4194, "region": "North America"},
    "Berlin": {"lat": 52.5200, "lon": 13.4050, "region": "Europe"},
    
    # Water cities (emotional, creative)
    "Venice": {"lat": 45.4408, "lon": 12.3155, "region": "Europe"},
    "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729, "region": "South America"},
    "Lisbon": {"lat": 38.7223, "lon": -9.1393, "region": "Europe"},
    "Buenos Aires": {"lat": -34.6037, "lon": -58.3816, "region": "South America"},
}


def dignity_score(dignity: str) -> float:
    """Convert dignity string to numerical score."""
    return DIGNITY_SCORES.get(dignity, 0)


def is_angular(house: int) -> bool:
    """Check if house is angular (1, 4, 7, 10)."""
    return house in [1, 4, 7, 10]


def is_succedent(house: int) -> bool:
    """Check if house is succedent (2, 5, 8, 11)."""
    return house in [2, 5, 8, 11]


def is_cadent(house: int) -> bool:
    """Check if house is cadent (3, 6, 9, 12)."""
    return house in [3, 6, 9, 12]


def check_cazimi(planet_lon: float, sun_lon: float) -> bool:
    """
    Check if planet is cazimi (in the heart of the Sun).
    Cazimi: within 17' (0.283°) of exact conjunction with Sun.
    """
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return distance < 0.283


def check_under_beams(planet_lon: float, sun_lon: float) -> bool:
    """Check if planet is under the Sun's beams (< 17° from Sun)."""
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return distance < 17


def check_combust(planet_lon: float, sun_lon: float) -> bool:
    """Check if planet is combust (< 8° from Sun, not cazimi)."""
    distance = abs(planet_lon - sun_lon)
    if distance > 180:
        distance = 360 - distance
    return 0.283 < distance < 8


def is_diurnal_chart(chart: Dict) -> bool:
    """
    Determine if chart is diurnal (Sun above horizon) using houses.
    Houses 7-12 = above horizon (diurnal).
    """
    sun = next((p for p in chart.get('planets', []) if p['name'] == 'Sun'), None)
    if not sun:
        return True
    return sun.get('house') in [7, 8, 9, 10, 11, 12]


def check_mutual_reception(planet_a: Dict, planet_b: Dict, chart: Dict) -> bool:
    """
    Check if two planets are in mutual reception.
    Planet A in domicile/exaltation of Planet B, and vice versa.
    
    Simplified: Just check if each planet is in sign ruled by the other.
    """
    ruler_a_sign = get_ruler(planet_a['sign'])
    ruler_b_sign = get_ruler(planet_b['sign'])
    
    return (ruler_a_sign == planet_b['name'] and ruler_b_sign == planet_a['name'])


def score_dignities(chart: Dict) -> Tuple[float, Dict]:
    """
    Score 1: Essential Dignities (35 points max).
    Prioritize ASC ruler, MC ruler, then all planets.
    """
    score = 0
    details = {}
    
    # Get ASC and MC rulers
    asc_sign = chart.get('asc_sign', 'Aries')
    mc_sign = chart.get('mc_sign', 'Capricorn')
    
    asc_ruler_name = get_ruler(asc_sign)
    mc_ruler_name = get_ruler(mc_sign)
    
    # Find ASC and MC rulers in planets
    asc_ruler = None
    mc_ruler = None
    
    planets = chart.get('planets', [])
    for p in planets:
        if p['name'] == asc_ruler_name:
            asc_ruler = p
        if p['name'] == mc_ruler_name:
            mc_ruler = p
    
    # Score ASC ruler (double weight)
    if asc_ruler:
        # Extract degree from longitude (lon % 30)
        degree = asc_ruler['lon'] % 30
        dig_info = get_planet_dignity(asc_ruler['name'], asc_ruler['sign'], degree)
        dig = dig_info.get('kind', 'peregrine')
        dig_score = dig_info.get('score', 0)
        asc_score = dig_score * 2
        score += asc_score
        details['asc_ruler_dignity'] = {'planet': asc_ruler_name, 'dignity': dig, 'score': asc_score}
    
    # Score MC ruler (1.5x weight)
    if mc_ruler:
        degree = mc_ruler['lon'] % 30
        dig_info = get_planet_dignity(mc_ruler['name'], mc_ruler['sign'], degree)
        dig = dig_info.get('kind', 'peregrine')
        dig_score = dig_info.get('score', 0)
        mc_score = dig_score * 1.5
        score += mc_score
        details['mc_ruler_dignity'] = {'planet': mc_ruler_name, 'dignity': dig, 'score': mc_score}
    
    # Score all other planets (0.5x weight each)
    total_planet_score = 0
    for p in planets:
        degree = p['lon'] % 30
        dig_info = get_planet_dignity(p['name'], p['sign'], degree)
        dig_score = dig_info.get('score', 0)
        planet_score = dig_score * 0.5
        total_planet_score += planet_score
    
    score += total_planet_score
    details['all_planets_score'] = total_planet_score
    
    # Cap at 35
    final_score = min(score, 35)
    details['total'] = final_score
    
    return final_score, details


def score_angularity(chart: Dict) -> Tuple[float, Dict]:
    """
    Score 2: Angularity (25 points max).
    Benefics in angular houses = positive.
    Malefics in angular houses = neutral (unless well-aspected).
    
    Uses real house placements (1,4,7,10) for angularity.
    """
    score = 0
    planets = chart.get('planets', [])
    has_houses = any(p.get('house') for p in planets)
    details = {'angular_planets': []}
    if not has_houses:
        # Fallback to simplified proxy if we don't have houses
        details['note'] = 'No house data; using simplified proxy by dignities'
        for p in planets:
            planet_name = p['name']
            if planet_name in BENEFICS:
                score += 3
            elif planet_name in MALEFICS:
                degree = p['lon'] % 30
                dig_info = get_planet_dignity(planet_name, p['sign'], degree)
                if dig_info.get('kind') in ['domicile', 'exaltation']:
                    score += 1
        final_score = min(score, 25)
        details['total'] = final_score
        return final_score, details
    
    for p in planets:
        house = p.get('house')
        if not house or not is_angular(house):
            continue
        planet_name = p['name']
        planet_score = 0
        if planet_name in BENEFICS:
            planet_score = 8
        elif planet_name == 'Sun':
            planet_score = 6
        elif planet_name == 'Moon':
            planet_score = 5
        elif planet_name == 'Mercury':
            planet_score = 5
        elif planet_name in MALEFICS:
            degree = p['lon'] % 30
            dig = get_planet_dignity(planet_name, p['sign'], degree).get('kind', 'peregrine')
            planet_score = 3 if dig in ['domicile', 'exaltation'] else -2
        score += planet_score
        details['angular_planets'].append({'planet': planet_name, 'house': house, 'score': planet_score})
    
    # Cap at 25
    final_score = min(score, 25)
    details['total'] = final_score
    
    return final_score, details


def score_solar_conditions(chart: Dict) -> Tuple[float, Dict]:
    """
    Score 3: Solar Conditions (15 points max).
    Cazimi = +10, Under beams = -5, Combust = -10.
    """
    score = 0
    details = {'conditions': []}
    
    # Find Sun
    sun = next((p for p in chart.get('planets', []) if p['name'] == 'Sun'), None)
    if not sun:
        return 0, {'total': 0, 'conditions': []}
    
    sun_lon = sun['lon']
    
    for p in chart.get('planets', []):
        if p['name'] == 'Sun':
            continue
        
        planet_lon = p['lon']
        planet_name = p['name']
        condition_score = 0
        condition_state = 'free'
        
        if check_cazimi(planet_lon, sun_lon):
            condition_score = 10
            condition_state = 'cazimi'
        elif check_combust(planet_lon, sun_lon):
            condition_score = -10
            condition_state = 'combust'
        elif check_under_beams(planet_lon, sun_lon):
            condition_score = -5
            condition_state = 'under_beams'
        
        if condition_state != 'free':
            score += condition_score
            details['conditions'].append({
                'planet': planet_name,
                'state': condition_state,
                'score': condition_score
            })
    
    # Cap between -10 and +15
    final_score = max(min(score, 15), -10)
    details['total'] = final_score
    
    return final_score, details


def score_aspects_reception(chart: Dict) -> Tuple[float, Dict]:
    """
    Score 4: Aspects with Reception (15 points max).
    Trine/sextile with reception = +5, without = +3.
    Square/opposition with reception = +1, without = -3.
    """
    score = 0
    details = {'aspects': []}
    
    aspects = chart.get('aspects', [])
    planets_dict = {p['name']: p for p in chart.get('planets', [])}
    
    for aspect in aspects:
        planet_a_name = aspect.get('a')
        planet_b_name = aspect.get('b')
        aspect_type = aspect.get('type')
        
        planet_a = planets_dict.get(planet_a_name)
        planet_b = planets_dict.get(planet_b_name)
        
        if not planet_a or not planet_b:
            continue
        
        has_reception = check_mutual_reception(planet_a, planet_b, chart)
        aspect_score = 0
        
        if aspect_type in ['trine', 'sextile']:
            aspect_score = 5 if has_reception else 3
        elif aspect_type in ['square', 'opposition']:
            aspect_score = 1 if has_reception else -3
        
        score += aspect_score
        details['aspects'].append({
            'planets': f"{planet_a_name} {aspect_type} {planet_b_name}",
            'reception': has_reception,
            'score': aspect_score
        })
    
    # Cap at 15
    final_score = min(score, 15)
    details['total'] = final_score
    
    return final_score, details


def score_sect(chart: Dict) -> Tuple[float, Dict]:
    """
    Score 5: Sect (10 points max).
    Diurnal: Jupiter angular/succedent = +5, Saturn not angular = +3.
    Nocturnal: Venus angular/succedent = +5, Mars not angular = +3.
    
    Uses houses to determine sect and placements.
    """
    score = 0
    details = {}
    
    # Determine sect
    # Fallback: if no houses, use simplified dignity-based proxy
    if not any(p.get('house') for p in chart.get('planets', [])):
        is_diurnal = (next((p for p in chart.get('planets', []) if p['name'] == 'Sun'), {'lon':0})['lon'] % 360) < 180
        details['sect'] = 'diurnal' if is_diurnal else 'nocturnal'
        details['note'] = 'No house data; using simplified proxy'
        jupiter = next((p for p in chart.get('planets', []) if p['name'] == 'Jupiter'), None)
        venus = next((p for p in chart.get('planets', []) if p['name'] == 'Venus'), None)
        if is_diurnal and jupiter:
            degree = jupiter['lon'] % 30
            dig_info = get_planet_dignity('Jupiter', jupiter['sign'], degree)
            if dig_info.get('kind') in ['domicile', 'exaltation']:
                score += 5
                details['jupiter_favorable'] = True
        if not is_diurnal and venus:
            degree = venus['lon'] % 30
            dig_info = get_planet_dignity('Venus', venus['sign'], degree)
            if dig_info.get('kind') in ['domicile', 'exaltation']:
                score += 5
                details['venus_favorable'] = True
        final_score = min(score, 10)
        details['total'] = final_score
        return final_score, details
    
    is_diurnal = is_diurnal_chart(chart)
    details['sect'] = 'diurnal' if is_diurnal else 'nocturnal'
    
    # Find sect planets
    jupiter = next((p for p in chart.get('planets', []) if p['name'] == 'Jupiter'), None)
    venus = next((p for p in chart.get('planets', []) if p['name'] == 'Venus'), None)
    saturn = next((p for p in chart.get('planets', []) if p['name'] == 'Saturn'), None)
    mars = next((p for p in chart.get('planets', []) if p['name'] == 'Mars'), None)
    
    if is_diurnal:
        # Diurnal: favor Jupiter angular/succedent, avoid Saturn angular
        if jupiter and jupiter.get('house') in [1, 4, 7, 10, 2, 5, 8, 11]:
            score += 5
            details['jupiter_favorable'] = True
        if saturn and not is_angular(saturn.get('house', 1)):
            score += 3
            details['saturn_not_angular'] = True
    else:
        # Nocturnal: favor Venus angular/succedent, avoid Mars angular
        if venus and venus.get('house') in [1, 4, 7, 10, 2, 5, 8, 11]:
            score += 5
            details['venus_favorable'] = True
        if mars and not is_angular(mars.get('house', 1)):
            score += 3
            details['mars_not_angular'] = True
    
    # Cap at 10
    final_score = min(score, 10)
    details['total'] = final_score
    
    return final_score, details


def score_solar_return_location(
    birth_date: datetime,
    city_name: str,
    city_lat: float,
    city_lon: float,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate and score a Solar Return chart for a specific location.
    
    Args:
        birth_date: Natal birth datetime (UTC)
        city_name: Name of the relocation city
        city_lat: Latitude of the city
        city_lon: Longitude of the city
        year: Year for SR (default: current year)
    
    Returns:
        Dictionary with total score, breakdown, and chart data
    """
    # Calculate SR chart for this location
    sr_result = solar_return_chart(birth_date, city_lat, city_lon, year)
    # Parse datetime and compute houses (Placidus)
    sr_dt = datetime.fromisoformat(sr_result['solar_return_datetime'].replace('Z', '+00:00'))
    # Try to compute houses; if fails, continue without houses
    enriched_planets = []
    asc_sign = 'Aries'
    mc_sign = 'Capricorn'
    try:
        houses_raw = calculate_houses(sr_dt, city_lat, city_lon, HOUSE_SYSTEM_PLACIDUS)
        cusps = houses_raw.get('cusps', [])
        if len(cusps) == 12:
            asc_sign, _ = longitude_to_sign_degree(houses_raw['asc'])
            mc_sign, _ = longitude_to_sign_degree(houses_raw['mc'])
            for p in sr_result['planets']:
                lon = p.get('lon')
                house_num = get_planet_house(lon, cusps) if lon is not None else None
                p2 = dict(p)
                p2['house'] = house_num
                enriched_planets.append(p2)
        else:
            enriched_planets = list(sr_result['planets'])
    except Exception:
        enriched_planets = list(sr_result['planets'])
    chart = {
        'planets': enriched_planets,
        'aspects': sr_result['aspects'],
        'asc_sign': asc_sign,
        'mc_sign': mc_sign,
        'solar_return_datetime': sr_result['solar_return_datetime']
    }
    
    # Score using Persian criteria (simplified for MVP)
    dig_score, dig_details = score_dignities(chart)
    ang_score, ang_details = score_angularity(chart)
    sol_score, sol_details = score_solar_conditions(chart)
    rec_score, rec_details = score_aspects_reception(chart)
    sec_score, sec_details = score_sect(chart)
    
    total_score = dig_score + ang_score + sol_score + rec_score + sec_score
    
    return {
        'city': city_name,
        'coordinates': {'lat': city_lat, 'lon': city_lon},
        'total_score': round(total_score, 2),
        'breakdown': {
            'dignities': dig_details,
            'angularity': ang_details,
            'solar_conditions': sol_details,
            'aspects_reception': rec_details,
            'sect': sec_details
        },
        'chart_summary': {
            'asc_sign': chart.get('asc_sign'),
            'mc_sign': chart.get('mc_sign'),
            'solar_return_datetime': sr_result['solar_return_datetime']
        }
    }


def rank_solar_return_locations(
    birth_date: datetime,
    year: Optional[int] = None,
    city_names: Optional[List[str]] = None,
    top_n: int = 3
) -> Dict[str, Any]:
    """
    Rank multiple cities for Solar Return relocation.
    
    Args:
        birth_date: Natal birth datetime (UTC)
        year: Year for SR (default: current year)
        city_names: List of city names to evaluate (default: all 16)
        top_n: Number of top recommendations to return
    
    Returns:
        Dictionary with rankings, top recommendations, and metadata
    """
    # Use all cities if not specified
    if not city_names:
        city_names = list(RELOCATION_CITIES.keys())
    
    # Score each city
    rankings = []
    for city_name in city_names:
        city_data = RELOCATION_CITIES.get(city_name)
        if not city_data:
            continue
        
        result = score_solar_return_location(
            birth_date,
            city_name,
            city_data['lat'],
            city_data['lon'],
            year
        )
        result['region'] = city_data['region']
        rankings.append(result)
    
    # Sort by total_score (descending)
    rankings.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Get top N
    top_cities = rankings[:top_n]
    
    return {
        'top_recommendations': [r['city'] for r in top_cities],
        'rankings': rankings,
        'criteria': 'Persian/Hellenistic (dignities, angularity, sect, reception, solar conditions)',
        'cities_analyzed': len(rankings),
        'year': year or datetime.utcnow().year
    }
