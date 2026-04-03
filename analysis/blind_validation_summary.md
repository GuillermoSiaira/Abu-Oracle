# Validación Cualitativa — Resumen de Cartas Ciegas

> Tabla agregada de todos los experimentos BV completados.
> Fuente canónica: `data/blind_validation/BV_index.json` + fichas individuales `data/blind_validation/BV_NNN_*.md`
> Para el protocolo completo, ver `BLIND_VALIDATION_PROTOCOL.md` (raíz del repo).
> Última actualización: 2026-04-03

---

## ¿Qué valida este corpus?

La validación cualitativa evalúa al **agente interpretativo Lilly** — no al Harmony Field.
Es complementaria e independiente de la validación cuantitativa HF↔eventos.

| Tipo | Objeto | Método |
|---|---|---|
| Cuantitativa | Harmony Field (campo geográfico) | Correlación HF↔eventos; Cohen's d |
| Cualitativa | Lilly (interpretación doctrinal) | Experimentos de carta ciega |

---

## Tabla de experimentos

| ID | Alias | Rodden | Fecha exp. | Estado | Dimensiones ✅ | ¿Valida? |
|---|---|---|---|---|---|---|
| BV_001 | Mr. X | AA | 2026-04-03 | Completado | 4/5 | ✅ Sí |

**Objetivo:** 20 experimentos completados antes de ronda seed.  
**Progreso:** 1/20

---

## Detalle BV_001 — Mr. X (Trump, 14 Jun 1946 / Nueva York)

### Inferencias verificadas

| Dimensión | Score | Descripción |
|---|---|---|
| Perfil de carácter | ✅ | "La arquitectura es soberana" — coherente con perfil verificado |
| Dominio dominante | ✅ | Casa 10 con Saturno en detrimento — reputación comprometida estructuralmente |
| Período de crisis | ✅ | Clúster abril 2026 (Saturno opone ASC, Marte cuadra Sol/Luna) — coherente |
| Señor del año | ✅ | Casa 8 / Venus peregrina — año de liquidación |
| Tránsitos lentos | ⏳ | Saturno opone ASC abril 2026 — pendiente verificación ex-post |

### Configuraciones doctrinales más significativas

- **Júpiter peregrino en Casa 1**: vitalidad expansiva sin elegancia cortesana
- **Saturno en detrimento en Casa 10**: tensión estructural sobre autoridad pública
- **Fortuna + Espíritu en Aries bajo Marte peregrino Casa 11**: palanca opera a través de redes y colectivos
- **Eclipse solar agosto 2026 en Casa 11**: alianzas y redes de apoyo afectadas

### Observación del verificador

> *"Es sorprendente el análisis que logra realizar, dado que yo sí conozco la identidad de la persona."*  
> — Guillermo Siaira, 2026-04-03

---

## Metodología de scoring

### Escala por dimensión

| Símbolo | Significado |
|---|---|
| ✅ | Alta coherencia — la inferencia coincide sin ambigüedad con el hecho verificable |
| ⚠️ | Coherencia parcial — compatible pero demasiado general |
| ❌ | Divergencia — la inferencia contradice el hecho verificable |
| ⏳ | Pendiente — el período referido aún no ha ocurrido |

### Umbral de validación

Un experimento **valida** si obtiene ✅ en ≥ 4 de 5 dimensiones y ningún ❌.

### Dimensiones evaluadas

1. Perfil de carácter (secta, benéfico, maléfico)
2. Dominio de vida dominante
3. Período de crisis/auge
4. Señor del año (profección)
5. Tránsitos lentos sobre ángulos

---

## Script de automatización

```bash
python scripts/blind_validation/run_blind_validation.py \
  --date 1946-06-14 --time 10:54 \
  --lat 40.7128 --lon -74.0060 \
  --alias "Mr. X" \
  --subject-real "Donald Trump" \
  --rodden AA
```

Genera automáticamente la ficha en `data/blind_validation/` y la nota Obsidian en `obsidian_vault/03_experimentos/`.
