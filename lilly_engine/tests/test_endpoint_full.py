import pytest
import httpx
import traceback

# Payload mínimo válido para el endpoint
MINIMAL_ANALYSIS_FIXTURE = {
    "planets": [
        {"name": "Sun", "sign": "Aries", "degree": 10, "longitude": 10.0, "house": 1, "dignity": "domicile"},
        {"name": "Moon", "sign": "Taurus", "degree": 5, "longitude": 35.0, "house": 2, "dignity": "exaltation"}
    ],
    "houses": [
        {"number": 1, "sign": "Aries", "degree": 0, "longitude": 0.0},
        {"number": 2, "sign": "Taurus", "degree": 30, "longitude": 30.0}
    ],
    "aspects": []
}

import os
ENDPOINT_URL = os.getenv("LILLY_URL", "http://localhost:8001") + "/api/ai/interpret/full"

@pytest.mark.parametrize("payload", [
    {
        "analysis": MINIMAL_ANALYSIS_FIXTURE,
        "question": "¿Qué debería trabajar este mes?",
        "language": "es"
    }
])
def test_interpret_full_endpoint(payload):
    try:
        response = httpx.post(ENDPOINT_URL, json=payload, timeout=60)
        assert response.status_code == 200, f"HTTP status {response.status_code} != 200"
        data = response.json()
        assert "maestro" in data, "No se encontró 'maestro' en la respuesta"
        assert "ai" in data, "No se encontró 'ai' en la respuesta"
        ai = data["ai"]
        assert ai is not None, "Campo 'ai' es None (posible error de API key o GPT)"
        assert "headline" in ai, "No se encontró 'headline' en 'ai'"
        assert "narrative" in ai, "No se encontró 'narrative' en 'ai'"
        assert "actions" in ai, "No se encontró 'actions' en 'ai'"
        print("\n--- TEST EXITOSO ---")
        print("Payload enviado:", payload)
        print("Respuesta recibida:", data)
    except Exception as e:
        print("\n--- TEST FALLIDO ---")
        print("Tipo de error:", type(e).__name__)
        print("Mensaje:", str(e))
        print("Stacktrace:")
        traceback.print_exc()
        print("Payload enviado:", payload)
        try:
            print("Respuesta recibida:", response.text)
        except Exception:
            print("No se pudo obtener la respuesta.")
        print("\nAnálisis técnico del posible origen:")
        if 'response' in locals() and response.status_code == 401:
            print("- Error de autenticación. Verifica la API key de OpenAI.")
        elif 'response' in locals() and response.status_code == 500:
            print("- Error interno del servidor. Revisa logs de Lilly Engine.")
        elif 'response' in locals() and response.status_code == 422:
            print("- Payload inválido. Revisa el formato y los campos requeridos.")
        else:
            print("- Error desconocido. Revisa la configuración y los logs.")
        assert False, "Test fallido por excepción. Ver logs arriba."

# Instrucciones para ejecutar:
# 1. Asegúrate de que Lilly Engine esté corriendo en localhost:8001
# 2. Ejecuta: pytest lilly_engine/tests/test_endpoint_full.py --capture=no
# 3. Revisa la salida para el reporte completo
