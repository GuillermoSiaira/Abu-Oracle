# Abu Oracle – Arquitectura Híbrida

## Flujo de Optimización Geográfica

```mermaid
flowchart TD
    A[Request] --> B[Classic Engine (Filter)]
    B --> C[Top 20 Cities]
    C --> D[Quantum Solver (QAOA)]
    D --> E[Optimal City]
```

## Descripción del Flujo

1. **Request:** El usuario envía los datos natales y parámetros de optimización.
2. **Classic Engine (Filter):** El motor clásico filtra ~10,000 ciudades y selecciona el Top 20 según criterios astrológicos tradicionales.
3. **Quantum Solver (QAOA):** El Top 20 es re-evaluado usando un algoritmo cuántico (QAOA) que minimiza la tensión astrológica mediante un Hamiltoniano personalizado.
4. **Optimal City:** Se retorna la ciudad óptima y el score energético cuántico.

## Componentes Clave
- **Motor Clásico:** Algoritmos heurísticos y reglas astrológicas tradicionales.
- **Quantum Layer:** Qiskit + QAOA + Hamiltoniano astrológico + gaussian_influence.
- **API Híbrida:** Endpoint `/api/igp/optimize-quantum` para integración y consulta.
