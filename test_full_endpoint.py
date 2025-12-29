import httpx
import json

def test_full_endpoint():
    url = "http://localhost:8001/api/ai/interpret/full"
    payload = {
        "analysis": {
            "person": {"name": "Test", "question": ""}
        },
        "question": "¿Qué sabes hacer?",
        "language": "es"
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = httpx.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, timeout=30)
    except Exception as e:
        print(f"ERROR: No se pudo conectar al endpoint: {e}")
        return
    print(f"Status code: {response.status_code}")
    print(f"Headers: {response.headers}")
    try:
        data = response.json()
        print("Response JSON:", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: El body no es JSON válido: {e}")
        print("Body recibido:", response.text)
        return
    # Validaciones estrictas
    keys = set(data.keys())
    expected = {"maestro", "narrative", "ai_response"}
    if response.status_code != 200:
        print(f"ERROR: status_code esperado 200, recibido {response.status_code}")
    if not expected.issubset(keys):
        print(f"ERROR: El JSON no contiene todas las claves esperadas: {expected - keys}")
    else:
        print("✓ El endpoint responde correctamente y cumple el contrato.")

if __name__ == "__main__":
    test_full_endpoint()
