import requests

URL = "http://localhost:8000/api/astro/chart/extended"

def probe(name, date, lat, lon):
    print(f"🕵️ Probando {name} ({date})...", end=" ")
    try:
        response = requests.get(URL, params={"date": date, "lat": lat, "lon": lon}, timeout=5)
        if response.status_code == 200:
            print("✅ OK")
        else:
            print(f"❌ ERROR {response.status_code}")
    except Exception as e:
        print(f"⛔ EXCEPCIÓN: {e}")

print("--- DIAGNÓSTICO DIFERENCIAL ---")

# 1. CASO CONTROL (Moderno + Buenos Aires) -> Debería funcionar si el motor está vivo
probe("Control (Hoy)", "2023-01-01T12:00:00", -34.60, -58.38)

# 2. HIPÓTESIS FECHA (Mismo lugar, fecha antigua) -> Si falla, es Python en Windows
probe("Test Fecha (1875)", "1875-07-26T19:29:00", -34.60, -58.38)

# 3. HIPÓTESIS CIUDAD (Jung real) -> Si el anterior funcionó y este falla, es la ubicación
probe("Jung (Kesswil)", "1875-07-26T19:29:00", 47.60, 9.35)