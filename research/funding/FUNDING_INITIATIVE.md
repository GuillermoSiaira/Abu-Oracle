# Abu Oracle — Iniciativa de Financiamiento de Investigación

> Documento maestro. Última actualización: 2026-04-03.
> Para pitches individuales ver: PITCH_ANTHROPIC.md · PITCH_GOOGLE.md · PITCH_OPTIMISM.md

---

## Resumen ejecutivo

Abu Oracle es un sistema de inteligencia biográfica personal construido sobre
doctrina astrológica helenística-persa, validado empíricamente con 5,359 cartas
natales y 527 eventos biográficos documentados (Cohen's d=0.44), desplegado en
producción con usuarios reales pagos.

El sistema genera un problema de investigación original que no existe en ningún
otro lugar: **cómo optimizar el costo de inferencia LLM en un SaaS multi-plan
con restricciones de margen por plan de suscripción**. Tenemos la formulación
teórica (MILP), el simulador calibrado, los hallazgos preliminares, y el sistema
real que motiva el problema.

**Lo que buscamos:** financiamiento para completar la calibración empírica
(Fase A-2: ~$6 en API) y para operar la plataforma de validación durante
6 meses mientras se acumulan los datos de distribución de rutas reales.

---

## Activos actuales — inventario

### Sistema en producción
- `app.abu-oracle.com` — desplegado el 19 de marzo de 2026
- Stack: Next.js + Python/FastAPI → Cloud Run (GCP) · Firebase Auth · Firestore
- Pago: USDC on-chain (Arbitrum One) → webhook Alchemy → provisioning automático
- Modelo de acceso: Genesis Member ($100 USDC · acceso de por vida · 100 slots)

### Corpus empírico
- 5,359 cartas natales geocodificadas (Rodden ratings A/AA/B)
- 527 eventos biográficos con coordenadas geográficas y valencia
- Harmony Field v3: campo escalar geográfico con validación estadística
  - H04 Hogar: Δcorr +0.306, Cohen's d +1.311
  - H05 Creatividad: Δcorr +0.155
  - H10 Carrera: Cohen's d_global +0.567 (N+=231, N−=4)
- Dataset procesado: `data/processed/hf_dataset_v2.parquet` (4,650 embeddings HF 36D)

### Motor de interpretación (Lilly)
- 11 rutas LLM activas: screen-open, planet, technique, city, domain, house,
  sky, transit, solar-return, chat + events
- Anthropic Claude Sonnet 4.6 / Haiku 4.5 según ruta
- Context Builder centralizado con memoria longitudinal por usuario (Firestore)
- `completeLilly()`: loop de continuación automático si stop_reason=max_tokens

### Módulo FinOps (investigación de ingeniería)
- `selectModel(route, plan)` — gateway unificado de selección de modelo
- MILP formulado: variables x_r (modelo) y t_{u,r} (max_tokens) por ruta × plan
- Simulador de carga (`scripts/finops/load_simulator.py`):
  - 500-800 usuarios simultáneos, Poisson arrivals
  - Dos políticas: static_baseline vs greedy_approximation
  - Modela: cache hit, completeLilly() continuation, R5 min_margin, shadow prices
- Fase A-1 completa: 495 mediciones de tokens de input ($0, sin generación)
- Fase A-2 diseñada: experimento de output tokens (~$6, pendiente de ejecución)

---

## El problema de investigación

### Formulación

Ningún paper existente aborda la optimización de costos de LLM con restricciones
de margen **por plan de suscripción**. FrugalGPT optimiza costo global sin modelo
de negocio. RouteLLM optimiza calidad sin restricciones de margen.
Abu Oracle necesita — y está construyendo — un optimizador que conoce:

```
Para cada usuario u con plan p, ruta r:
  min  E[costo(r, model, max_tokens)]
  s.t. P(truncación | max_tokens) ≤ ε_r     (calidad mínima)
       E[costo(r)] ≤ budget(plan, r)         (margen por plan)
       Σ_r rpm(r) ≤ TIER2_RPM               (rate limit compartido)
       Σ_r tpm(r) ≤ TIER2_TPM
```

Variables de decisión:
- `x_r ∈ {Haiku, Sonnet}` — elección de modelo por ruta (discreta)
- `t_{u,r} ∈ Z+` — max_tokens por ruta × plan (continua)

### Por qué es publicable

1. **Sistema real, no simulación hipotética.** El MILP no es un ejercicio teórico —
   es la arquitectura de costo de un SaaS en producción con usuarios reales pagos.

2. **Resultado empírico novedoso.** El Harmony Field es el primer campo escalar
   geográfico basado en doctrina astrológica validado estadísticamente contra
   eventos biográficos reales. Eso por sí solo es publicable en un venue diferente.

3. **Contribución conceptual limpia.** El shadow price del TPM es una propiedad
   del optimizador, no del tráfico. Sin política con noción de margen marginal,
   el shadow price es invisible y la decisión de upgrade de tier es ciega.

**Venues candidatos:** MLSys · SIGMOD · ACL Workshop on Efficiency · AAAI

---

## Hallazgos preliminares (bajo supuestos explícitos)

Simulación: 500-800 usuarios · 60 min · seed=42 · distribución planes genesis/annual/monthly

| Hallazgo | Resultado | Estado |
|----------|-----------|--------|
| θ — umbral shadow price TPM | 700 usuarios | Bajo supuestos sintéticos |
| Shadow price a N=700 (greedy) | $0.0055/min pico | Idem |
| Shadow price a N=800 (greedy) | $0.0183/min pico (3.3× no lineal) | Idem |
| Política estática: margen total | −$6.76 a −$10.80 (según N) | Idem |
| Greedy_approximation: margen total | +$11.24 a +$18.12 (según N) | Idem |
| Genesis: plan menos rentable | −$0.012/req avg | Refuta hipótesis de pricing |
| RPM: no es cuello de botella | pico 19.2% en N=800 | TPM es el recurso escaso |
| R5 binding | 29-31% de requests en greedy | Activo de forma consistente |

**Lo que convierte estos resultados en paper:** calibración empírica de
P_CONTINUATION, distribución de output tokens y distribución de rutas reales.
Los tres salen de Fase A-2 + 6 meses de logs de producción.

---

## Qué desbloquea el financiamiento

### Fase A-2 — $6 (ejecutable ahora)
- Medición real de output_tokens por ruta (50 sujetos × 11 rutas × generación real)
- Calibra: P_CONTINUATION real, distribución de output tokens por ruta
- Convierte los hallazgos de "bajo supuestos" a "calibrados empíricamente"

### Operación 6 meses — $200-400/mes
- Cloud Run: ~$50-80/mes (compute actual)
- Anthropic API: ~$50-150/mes (usuarios reales generando distribución real de rutas)
- Datos resultantes: distribución real de rutas, P_CONTINUATION real, logs de uso
- Esto completa el tercer parámetro que Fase A-2 no provee

### Tiempo de investigación — el activo más escaso
- Fase B: formular y resolver el MILP con datos de Fase A-2
- Fase C: caching avanzado (contextBlock estático/dinámico)
- Fase D: auditoría de tokens del contextBlock
- Redacción del paper: ~4 semanas con los datos de A-2

**Presupuesto total para paper submission-ready: $2,000-4,000 USD**
(principalmente tiempo + API costs de A-2 + operación 6 meses)

---

## El ángulo ERC-8004

Abu Oracle ya tiene la infraestructura base de un agente autónomo on-chain:

| Componente | Estado actual |
|-----------|---------------|
| Pago on-chain (USDC/Arbitrum) | ✅ Producción |
| Webhook detection (Alchemy) | ✅ Producción |
| Provisioning automático (Firebase) | ✅ Producción |
| Email de bienvenida automático (Resend) | ✅ Producción |
| selectModel() — gateway de costo | ✅ Producción |
| MILP optimizer | ⏳ Fase B (pendiente A-2) |
| Reinversión autónoma en infraestructura | ❌ Pendiente |

**ERC-8004** es el estándar emergente para agentes autónomos on-chain con
identidad verificable. Un Abu Oracle ERC-8004 podría:

1. Recibir pago on-chain → provisionar acceso automáticamente (ya funciona)
2. Ejecutar el MILP en cada sesión → decidir qué modelo usar por request
3. Medir shadow prices en tiempo real → decidir cuándo subir de tier
4. Reinvertir el margen generado en infraestructura sin intervención humana

El paper de FinOps es el sustento técnico de ese agente. El MILP no es solo
una optimización de costos — es el cerebro económico del agente autónomo.

**Relevancia para funding crypto:** el ERC-8004 convierte Abu Oracle de un
SaaS con pago crypto a infraestructura de agentes autónomos con base empírica
verificable on-chain. Arbitrum, Optimism y a16z crypto financian exactamente esto.

---

## Estrategia por funder

| Funder | Ángulo principal | Ask | Probabilidad |
|--------|-----------------|-----|--------------|
| Anthropic | Conocimiento público sobre optimización de su API | Research grant + API credits | Alta |
| Google Research Credits | GCP user + LLM optimization research | $5,000-10,000 en credits | Alta |
| Optimism RetroPGF | Impacto demostrado, open source del simulador | $5,000-20,000 USDC | Media |
| Arbitrum DAO | ERC-8004 + infraestructura de agentes | $10,000-30,000 USDC | Media |
| LabDAO | Investigador independiente, compute grant | $2,000-5,000 en compute | Media |

Ver archivos individuales para pitches específicos.

---

## Estado de la iniciativa

| Tarea | Estado |
|-------|--------|
| Documento maestro | ✅ Este archivo |
| Pitch Anthropic | ✅ PITCH_ANTHROPIC.md |
| Pitch Google | ✅ PITCH_GOOGLE.md |
| Pitch Optimism/Arbitrum | ✅ PITCH_OPTIMISM.md |
| Ejecutar Fase A-2 | ⏳ Pendiente autorización |
| Open source del simulador | ⏳ Pendiente decisión |
| Deploy ERC-8004 | ⏳ Pendiente decisión |

---

*Contacto: Guillermo Siaira · guillermosiaira@gmail.com*
*Sistema: app.abu-oracle.com · Landing: abu-oracle.com*
