# FinOps — Análisis de Escalabilidad

**Objetivo:** encontrar θ — el umbral de N_USERS donde el shadow price del TPM
se activa por primera vez (>95% saturación sostenida).

**Configuración fija:** seed=42 · 60 minutos · 10 req/usuario/hr
· distribución de planes: genesis 10% / annual 30% / monthly 60%
· Tier 2: 1,000 RPM / 450,000 TPM

---

## Tabla comparativa — Margen total (USD)

| N_USERS | Margen static | Margen greedy | Delta greedy−static |
|---------|--------------|--------------|---------------------|
| 500     | −$6.76       | +$11.24      | +$18.00             |
| 600     | −$9.72       | +$12.62      | +$22.34             |
| 700     | −$10.01      | +$15.92      | +$25.93             |
| 800     | −$10.80      | +$18.12      | +$28.92             |

**Nota:** la política estática tiene margen negativo en todos los escenarios.
La greedy_approximation es rentable desde N=500 y el delta absoluto crece con la carga
— el valor del optimizador aumenta a medida que el sistema escala.

---

## Tabla comparativa — TPM utilization pico (por minuto)

| N_USERS | TPM pico static | TPM pico greedy | Dropped static | Dropped greedy | Drop rate static | Drop rate greedy |
|---------|----------------|----------------|---------------|---------------|-----------------|-----------------|
| 500     | 94.72%         | 88.38%         | 0             | 0             | 0.0%            | 0.0%            |
| 600     | 99.75%         | 99.39%         | 14            | 8             | 0.23%           | 0.13%           |
| 700     | 99.55%         | 99.64%         | 50            | 28            | 0.71%           | 0.40%           |
| 800     | 99.98%         | 100.0%         | 230           | 153           | 2.87%           | 1.91%           |

---

## Tabla comparativa — Shadow prices y R5

| N_USERS | Shadow TPM static | Shadow TPM greedy | Shadow RPM (ambas) | R5 applied (greedy) | Revenue lost static | Revenue lost greedy |
|---------|-------------------|-------------------|--------------------|---------------------|--------------------|--------------------|
| 500     | $0.000000         | $0.000000         | $0.000000          | 1,552               | $0.0000            | $0.0000            |
| 600     | $0.000000         | $0.000000         | $0.000000          | 1,853               | $0.1937            | $0.1290            |
| 700     | $0.000000         | **$0.005523**     | $0.000000          | 2,094               | $0.7146            | $0.3960            |
| 800     | $0.000000         | **$0.018288**     | $0.000000          | 2,354               | $3.2143            | $2.1195            |

---

## θ — Umbral de activación del shadow price

**θ = 700 usuarios** (greedy_approximation).

El shadow price del TPM se activa por primera vez en N=700 bajo la política
greedy_approximation, con valor **$0.005523 USD** en el minuto de mayor saturación.

En N=800 el shadow price sube a **$0.018288 USD** — el valor económico de
1 token adicional de capacidad en el pico crece ~3.3× entre N=700 y N=800.

**La política estática no activa shadow price en ningún escenario** (N≤800)
porque sus drops son inelásticos: al llegar al límite simplemente descarta
requests sin haber intentado optimizar el uso de los tokens disponibles.
El shadow price requiere que el sistema esté cerca del límite Y tomando
decisiones marginales de asignación — condición que solo cumple greedy.

### Interpretación para el paper

El shadow price del TPM a N=700 cuantifica el valor marginal de subir de tier:
cada 1,000 tokens adicionales de capacidad valen ~$5.52 en ese minuto pico.
Escalado a la hora completa bajo carga sostenida de 700 usuarios, el valor
de subir al siguiente tier (TPM ilimitado) supera el costo incremental del tier
en aproximadamente 2-3 sesiones de uso.

---

## Observaciones adicionales

**RPM no es el cuello de botella.** El RPM pico máximo observado es 19.2%
(N=800, static). El límite de 1,000 RPM de Tier 2 no se acerca a saturarse —
el cuello de botella es exclusivamente TPM. La política greedy lo reduce porque
degrada rutas elegibles a Haiku (tokens por request 40-60% menores).

**Genesis sigue siendo el plan menos rentable.** En todos los escenarios el
margen del plan Genesis es negativo (avg −$0.012/req). La hipótesis de que
`$100/3000 sesiones = $0.0333/sesión` compensa el costo de API es incorrecta
bajo los supuestos actuales: el costo real por sesión Sonnet (~$0.15/sesión)
supera el revenue imputado. Implicación: el precio de Genesis ($100 one-time)
necesita revisión o el acceso debe estar condicionado a uso moderado (<5 req/día).

**Greedy reduce revenue lost en todos los escenarios.** Al degradar a Haiku
en rutas elegibles, los requests consumen menos TPM → menos drops por saturación
→ menos revenue perdido. En N=800: static pierde $3.21, greedy pierde $2.12
(34% menos revenue perdido).

**R5 crece con la carga.** A N=500, R5 aplica en 1,552 requests (31%).
A N=800, aplica en 2,354 (29.4%). La proporción es estable — el piso de margen
es binding de forma consistente, no solo en picos.

---

## Conclusión operativa

Para Abu Oracle al lanzamiento (estimado 100-200 usuarios activos simultáneos),
el sistema opera bien dentro del Tier 2. El umbral crítico es **θ ≈ 600-700
usuarios activos simultáneos** — a partir de ahí los drops y el shadow price
indican que el costo de no subir de tier es económicamente medible.

La greedy_approximation justifica su complejidad adicional únicamente
por la mejora de margen: +$18-29 USD por hora de carga sostenida a escala.
Extrapolado a un mes (720 horas, 70% uptime ≈ 504 horas productivas):
**+$9,072–14,581 USD/mes de margen adicional** a N=500-800 usuarios.

---

*Generado: 2026-04-03*
*Script: `scripts/finops/load_simulator.py`*
*Nota: greedy_approximation es un heurístico derivado de la estructura del MILP,
no una solución LP exacta. Ver `research/finops/MILP_INITIATIVE.md`.*
