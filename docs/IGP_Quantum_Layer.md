# IGP Quantum Layer

## Resumen
El módulo IGP Quantum Layer integra computación cuántica (Qiskit) para optimizar la selección de ubicaciones geográficas astrológicas. Utiliza un enfoque híbrido: primero filtra ciudades con el motor clásico y luego aplica QAOA (Quantum Approximate Optimization Algorithm) sobre el Top 20 usando un Hamiltoniano de Tensión Astrológica.

## Algoritmo y Arquitectura
- **Qiskit** resuelve un problema QUBO (Quadratic Unconstrained Binary Optimization) para encontrar la ciudad óptima.
- La función objetivo minimiza la "tensión" entre los ángulos de la ciudad (ASC/MC) y los planetas natales/tránsitos.
- El Hamiltoniano modela la energía astrológica como suma de influencias planetarias y angulares.

## gaussian_influence
A diferencia de la lógica booleana clásica (presencia/ausencia de aspecto), `gaussian_influence` mide la intensidad de cada aspecto usando una campana de Gauss. Esto permite ponderar gradualmente la influencia astrológica:

- **Clásico:** Un aspecto existe o no.
- **Cuántico:** Cada aspecto tiene una intensidad continua según su proximidad angular, modelada por una función gaussiana.

## Flujo de trabajo
1. El motor clásico filtra 10,000 ciudades y selecciona el Top 20.
2. El Quantum Solver (QAOA) reevalúa el Top 20 usando el Hamiltoniano astrológico.
3. Se retorna la ciudad óptima y el score energético cuántico.

## Referencias
- [Qiskit](https://qiskit.org/)
- [QAOA](https://qiskit.org/documentation/algorithms/qaoa.html)
- [Quadratic Unconstrained Binary Optimization](https://en.wikipedia.org/wiki/Quadratic_unconstrained_binary_optimization)
