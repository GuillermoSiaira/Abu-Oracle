import json
import os
import requests
import sys
from datetime import datetime

# ================= CONFIGURACIÓN =================
ABU_ENGINE_URL = "http://localhost:8000/api/astro/chart/extended"
GOLD_STANDARD_DIR = "data/gold_standard"
# =================================================

def print_header():
    print("\n" + "="*70)
    print(f" 🧪  ABU ORACLE | GOLD STANDARD INTEGRATION TEST")
    print(f"     Layer 1 (Data) --> Layer 2 (Engine)")
    print("="*70 + "\n")

def validate_file_structure(data, filename):
    """Verifica la integridad estructural del JSON (Schema v1.2)"""
    errors = []
    
    # Chequeo de Meta
    if 'meta' not in data: errors.append("Missing 'meta' block")
    if 'schema_version' not in data.get('meta', {}): errors.append("Missing 'schema_version'")
    
    # Chequeo de Birth Data
    bd = data.get('birth_data', {})
    if 'date_iso' not in bd: errors.append("Missing 'date_iso'")
    if 'location' not in bd: errors.append("Missing 'location'")
    
    # Chequeo de Eventos (Validación de higiene)
    events = data.get('biographical_events', [])
    for idx, ev in enumerate(events):
        if 'validation_target' not in ev: 
            errors.append(f"Event #{idx} missing 'validation_target'")
        elif 'axiom_id' not in ev['validation_target']:
             errors.append(f"Event #{idx} missing 'axiom_id' in target")
             
    return errors

def run_integration_test():
    print_header()
    
    if not os.path.exists(GOLD_STANDARD_DIR):
        print(f"❌ CRITICAL: Directory '{GOLD_STANDARD_DIR}' not found.")
        return

    files = [f for f in os.listdir(GOLD_STANDARD_DIR) if f.endswith(".json")]
    files.sort()
    
    if not files:
        print("⚠️  WARNING: No JSON files found in directory.")
        return

    success_count = 0
    
    for filename in files:
        filepath = os.path.join(GOLD_STANDARD_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ {filename} -> INVALID JSON FORMAT")
                continue

        # 1. Validación Estructural (Static Analysis)
        meta = data.get('meta', {})
        subject = meta.get('name', 'Unknown')
        rating = meta.get('rodden_rating', 'XX')
        
        print(f"📄 Processing: {filename} | {subject} (Rating: {rating})")
        
        structure_errors = validate_file_structure(data, filename)
        if structure_errors:
            print(f"   ⚠️  SCHEMA VIOLATIONS:")
            for err in structure_errors:
                print(f"      - {err}")
            print("-" * 70)
            continue # Saltamos al siguiente si el schema está mal

        # 2. Validación de Integración (API Call)
        bd = data['birth_data']
        payload = {
            "date": bd['date_iso'],
            "lat": bd['location']['lat'],
            "lon": bd['location']['lon']
        }
        
        try:
            start_ts = datetime.now()
            # Simulamos un timeout corto para exigir performance
            response = requests.get(ABU_ENGINE_URL, params=payload, timeout=5)
            duration = (datetime.now() - start_ts).total_seconds()
            
            if response.status_code == 200:
                engine_data = response.json()
                
                # Verificación mínima de que el motor devolvió algo coherente
                has_planets = 'planets' in engine_data.get('base_chart', {})
                
                if has_planets:
                    print(f"   ✅ API INTEGRATION OK ({duration:.3f}s)")
                    print(f"      Layer 1 Events Loaded: {len(data.get('biographical_events', []))}")
                    success_count += 1
                else:
                    print(f"   ❌ API RESPONSE MALFORMED (Missing 'planets')")
            else:
                print(f"   ❌ API ERROR: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("   ⛔ CONNECTION FAILED: Is Abu Engine running on port 8000?")
            break # Paramos todo si el motor está apagado
        except Exception as e:
            print(f"   ⚠️  RUNTIME EXCEPTION: {str(e)}")

        print("-" * 70)

    print(f"\n🏁 TEST COMPLETE: {success_count}/{len(files)} files passed integration.")

if __name__ == "__main__":
    run_integration_test()