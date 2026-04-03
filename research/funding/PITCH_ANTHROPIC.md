# Pitch — Anthropic Research Grant

> Ángulo: conocimiento público sobre optimización de la API de Anthropic.
> Canal: research@anthropic.com o contacto directo con el equipo de política de uso.

---

## Una línea

Abu Oracle está construyendo el primer optimizador de costos de LLM con
restricciones de margen por plan de suscripción — usando Claude como motor,
con un sistema en producción real como banco de prueba.

---

## El problema que estamos resolviendo (y que le importa a Anthropic)

La mayoría de los desarrolladores que usan la API de Anthropic toman decisiones
de modelo y max_tokens de forma heurística. No saben cuántos tokens realmente
consume cada tipo de request, cuándo la truncación genera una segunda llamada
(duplicando el costo), ni cómo el mix de modelos afecta su margen por plan de usuario.

Eso genera dos problemas que Anthropic tiene incentivo en resolver:
1. Los desarrolladores abandonan la API cuando el costo supera el margen.
2. Las decisiones subóptimas saturan innecesariamente el rate limit compartido.

**Estamos midiendo esto empíricamente y publicando los resultados.**

---

## Lo que tenemos

**Sistema en producción** (`app.abu-oracle.com`):
- 11 rutas que llaman a Claude Sonnet 4.6 / Haiku 4.5
- Usuarios reales pagos (Genesis: $100 USDC)
- Memoria longitudinal por usuario (Firestore)
- `completeLilly()`: detecta truncación → segunda llamada automática

**Corpus empírico** (investigación de base):
- 5,359 cartas natales · 527 eventos biográficos validados
- Campo escalar geográfico con Cohen's d=0.44 sobre eventos reales

**Módulo FinOps** (la investigación que financiaría este grant):
- MILP formulado: optimización de modelo × max_tokens por ruta × plan
- Simulador de carga construido y validado (500-800 usuarios simulados)
- Fase A-1 completa: 495 mediciones de tokens de input ($0, via count_tokens())
- Fase A-2 diseñada: medición de output tokens (~$6, pendiente)

**Hallazgos preliminares** (bajo supuestos — Fase A-2 los calibra empíricamente):
- θ=700 usuarios: umbral donde el shadow price del TPM se activa por primera vez
- El shadow price crece 3.3× entre N=700 y N=800 (no linealidad)
- La política estática de modelo tiene margen negativo estructural
- El shadow price es propiedad del optimizador, no del tráfico:
  sin política con noción de margen marginal, la decisión de upgrade de tier es ciega

---

## Qué pedimos

**Opción A — Research Grant + API Credits:**
- $5,000-10,000 USD para tiempo de investigación (6 meses)
- $2,000-5,000 en API credits para Fase A-2 y calibración continua

**Opción B — Solo API Credits:**
- $3,000-5,000 en Anthropic API credits
- El paper se produce igualmente; los credits aceleran la calibración

**Entregables a cambio:**
- Paper enviado a MLSys/SIGMOD con Anthropic mencionado en acknowledgments
- Código del simulador publicado como open source
- Dataset de distribución de tokens por tipo de request (útil para benchmarking)
- Blog post técnico sobre optimización de costos con la API de Anthropic

---

## Por qué le importa a Anthropic

1. **Conocimiento público sobre estructura de costos de la API.** No existe
   ningún paper que mida empíricamente P(truncación), distribución de output
   tokens y distribución de rutas reales en un sistema LLM en producción.

2. **El shadow price cuantifica el valor de subir de tier.** Eso es un argumento
   de venta para los plans de API — Anthropic no tiene esa métrica documentada.

3. **El simulador es reutilizable.** Cualquier equipo de Anthropic que quiera
   modelar el comportamiento de usuarios bajo rate limits puede usar este código.

4. **El resultado de Genesis** (plan menos rentable bajo configuración actual)
   tiene implicaciones directas para el pricing de API de Anthropic: la estructura
   de precios actuales desincentiva el uso intensivo en planes de acceso anticipado.

---

## Cronograma

| Mes | Actividad |
|-----|-----------|
| 1 | Fase A-2: medición de output tokens reales (~$6 API, 1 semana) |
| 1-2 | Calibración del simulador con datos reales |
| 2-3 | Fase B: resolver el MILP con datos de A-2 |
| 3-4 | Fase C-D: caching avanzado + auditoría de tokens |
| 4-5 | Redacción del paper |
| 6 | Submission a MLSys/SIGMOD |

---

## Contacto

Guillermo Siaira · guillermosiaira@gmail.com
Sistema: app.abu-oracle.com
Código: github.com/GuillermoSiaira/Abu-Oracle (privado — puede darse acceso)
Preliminary results: research/finops/scaling_analysis.md (disponible bajo solicitud)
