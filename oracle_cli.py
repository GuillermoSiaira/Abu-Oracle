import requests
import json
import time
import sys
import os

# --- CONFIGURACIÓN DE COLORES MATRIX ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# URLs de tus servicios (asumiendo que corren en Docker mapped a localhost)
ABU_URL = "http://localhost:8000"
LILLY_URL = "http://localhost:8001"

def type_writer(text, speed=0.03, color=GREEN):
    """Efecto de escritura tipo terminal antigua"""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write(RESET + "\n")

def print_matrix_loading():
    """Efecto visual de carga de datos"""
    data_stream = [
        "Conectando al Nodo Abu...",
        "Calculando Efemérides Suizas...",
        "Triangulando Vectores Planetarios...",
        "Sincronizando con Lilly Swarm...",
        "Estableciendo Enlace Neuronal..."
    ]
    print("\n")
    for line in data_stream:
        sys.stdout.write(f"{CYAN}[SYSTEM] {line}{RESET}\r")
        time.sleep(0.4)
        print(f"{GREEN}[OK] {line}{RESET}")
    print("\n")
from datetime import datetime

def get_chart_data():
    """Obtiene la carta natal con estructura PLANA (ISO Strings)"""
    
    # 1. Preparamos las fechas en formato texto ISO 8601
    # Formato: AAAA-MM-DDTHH:MM:SSZ
    birth_iso = "1978-07-05T21:15:00Z"
    
    now = datetime.utcnow()
    current_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 2. Estructura que coincide con main.py (BirthData / CurrentData)
    payload = {
        "birth": {
            "date": birth_iso,
            "lat": -37.84,   # Balcarce
            "lon": -58.25
        },
        "current": {
            "date": current_iso,
            "lat": -34.60,   # Buenos Aires
            "lon": -58.38
        },
        "person": {
            "name": "Operador",
            "question": "Estado actual del cielo"
        }
    }
    
    print(f"{YELLOW}>> Enviando coordenadas (Formato ISO)...{RESET}")
    
    try:
        response = requests.post(f"{ABU_URL}/analyze", json=payload)
        
        if response.status_code == 422:
            print(f"{RED}[ERROR DE FORMATO]{RESET}")
            print(f"{RED}Detalle: {response.text}{RESET}")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        print(f"\n{CYAN}--- ABU ENGINE DATA RECEIVED [SUCCESS] ---{RESET}")
        # Mostramos un resumen de los planetas calculados
        planets = data.get("chart", {}).get("planets", [])
        for p in planets[:5]: # Mostrar solo los primeros 5 para no llenar la pantalla
            name = p.get("name")
            sign = p.get("sign")
            print(f"{GREEN} > {name}: {sign}{RESET}")
            
        return data
        
    except Exception as e:
        print(f"{RED}[ERROR] Conexión fallida: {e}{RESET}")
        return None
        
def chat_session(context):
    """Bucle de chat con Lilly"""
    session_id = f"cli-session-{int(time.time())}"
    
    type_writer("\n>> LILLY SWARM ONLINE. El oráculo te escucha.", speed=0.05, color=BOLD+GREEN)
    
    while True:
        try:
            user_input = input(f"\n{YELLOW}TÚ >> {RESET}")
            if user_input.lower() in ['exit', 'quit', 'salir']:
                break
                
            # Llamada a Lilly
            payload = {
                "message": user_input,
                "session_id": session_id,
                "context": context # AQUÍ VIAJA EL GROUNDING
            }
            
            # Efecto de "Pensando"
            sys.stdout.write(f"{CYAN}Processing...{RESET}")
            sys.stdout.flush()
            
            response = requests.post(f"{LILLY_URL}/api/chat", json=payload)
            sys.stdout.write("\r" + " " * 20 + "\r") # Borrar "Processing..."
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "")
                print(f"{GREEN}LILLY >> {RESET}", end="")
                type_writer(ai_response, speed=0.02)
            else:
                print(f"{RED}[ERROR] Lilly no responde: {response.text}{RESET}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{RED}[ERROR] Conexión interrumpida: {e}{RESET}")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear') # Limpiar pantalla
    print(f"{BOLD}{GREEN}=== ABU ORACLE v0.1: TERMINAL UPLINK ==={RESET}")
    
    print_matrix_loading()
    
    # 1. Obtener Grounding (Contexto)
    chart_context = get_chart_data()
    
    if chart_context:
        # 2. Iniciar Chat
        chat_session(chart_context)
    else:
        print("Abortando misión.")