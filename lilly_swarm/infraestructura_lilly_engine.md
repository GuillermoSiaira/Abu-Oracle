# Lilly Engine – Infraestructura y Estructura de Carpetas

## 1. Dockerfile (`lilly_engine/Dockerfile`)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# Cloud Run provides PORT env var; default to 8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## 2. docker-compose.yml (raíz del proyecto)
```yaml
services:
  abu_engine:
    build: ./abu_engine
    container_name: abu_engine
    ports:
      - "8000:8000"
    restart: always

  lilly_engine:
    build: ./lilly_engine
    container_name: lilly_engine
    ports:
      - "8001:8001"
    restart: always
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - USE_ASSISTANTS=${USE_ASSISTANTS:-true}
      - ABU_URL=http://abu_engine:8000
      - OPENAI_ASSISTANT_ID=${OPENAI_ASSISTANT_ID}

  next_app:
    build: ./next_app
    container_name: next_app
    ports:
      - "3000:3000"
    restart: always
    environment:
      - NEXT_PUBLIC_ABU_URL=http://localhost:8000
      - NEXT_PUBLIC_LILLY_URL=http://localhost:8001
```

## 3. Estructura de Carpetas del Backend (`lilly_engine/`)
```
.lilly_engine/
├── .pytest_cache/
├── api_key_check.txt
├── archetypes.json
├── core/
├── data/
├── Dockerfile
├── json_maestro.py
├── lilly_logs.json
├── lilly_openai_logs.json
├── main.py
├── MULTILINGUAL.md
├── narrative_engine.py
├── requirements.txt
├── rules_persian.py
├── scripts/
├── tests/
├── test_context_manager.py
├── test_multilingual.py
├── test_output_contract.py
├── test_solar_return_interpret.py
├── utils.py
├── __init__.py
├── __pycache__/
```

---
Este archivo contiene toda la información solicitada para diagnóstico y consulta externa: Dockerfile, docker-compose.yml y estructura de carpetas del backend Lilly Engine.