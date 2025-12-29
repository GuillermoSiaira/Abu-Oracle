# 🧭 PROTOCOLO DE TRABAJO — AI_Oracle (Abu & Lilly)

## Estructura de repositorios
- El repositorio **ai-oracle** es el motor principal (Abu Engine + Lilly Engine + Next.js original).
- El repositorio **ai-oracle-v0-repo** es el sandbox visual, donde v0 genera la nueva UI.
- El segundo repo incluye al primero como subtree en `apps/ai_oracle/`.

## Roles
- **Copilot:** responsable de backend (motores Abu y Lilly), optimización, documentación y testing.
- **v0:** responsable de UI/UX experimental (`apps/v0_web/`), comunicación con endpoints del backend.
- **ChatGPT:** coordinación técnica, semántica LLM, documentación de decisiones y flujos.

## Backend goals (Copilot)
1. Mantener `/analyze` estable y con shape fijo.
2. Añadir endpoint `/analyze/contract` → retorna el JSON schema del contrato actual.
3. Revisar CORS (permitir localhost:3000).
4. Agregar caching a cálculos ephemeris y firdaria.
5. Asegurar que tests `pytest` pasen (`test_analyze_contract.py` incluido).
6. Documentar endpoints en `/docs` con ejemplos (FastAPI auto).
7. Preparar logs para depuración (modo verbose).

## Coordinación con v0
- v0 consumirá los endpoints `http://localhost:8000/analyze` y `/analyze/contract`.
- Copilot no debe cambiar el shape de salida sin avisar en commit BREAKING.
- Cada modificación en el backend debe quedar reflejada en `/docs/Analyze_Endpoint_Contract.md`.

## Workflow de branches
- `main`: estable (solo merges revisados).
- `backend-improvements`: rama de Copilot para mejoras internas.
- `v0-ui`: rama de v0 (frontend).

## Comunicación
- ChatGPT coordina. Cualquier cambio estructural debe pasar por este flujo:
  1. Copilot propone → 2. ChatGPT valida → 3. v0 adapta UI.
