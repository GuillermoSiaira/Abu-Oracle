# APÉNDICE C — CONTRATO DE AGENTE (Agent Contract)

**Fecha:** 2026-01-02  
**Autor:** Abu Oracle Project  
**Versión:** 1.0  
**Nota:** Documento normativo, diseñado para ingestión y validación por agentes de IA y humanos. Estructura y ejemplos listos para parsing automático y revisión manual.  
*Referencia axiomática: Axiomatics of Heavens v0.3*

---

## C.1 Propósito del Contrato
Define la **interfaz obligatoria**, restricciones y prohibiciones para todo agente intérprete (Lilly Swarm), garantizando:
- No violar la axiomática
- Separación entre interpretación y cálculo
- Auditoría y robustez bajo degradación

---

## C.2 Rol del Agente
Un agente es una **función interpretativa condicionada** que:
- recibe un **estado geométrico ya calculado**,
- aplica un **lenguaje interpretativo** de escuela,
- devuelve un **juicio estructurado** con incertidumbre explícita.

El agente **no calcula** ni decide arquitectura.

---

## C.3 Interfaz de Entrada (Input Contract)

### C.3.1 Estructura Mínima de Input
```json
{
  "astro_state": {
    "time_model": "solar_true | solar_mean | sidereal",
    "observer": {"lat": -34.6, "lon": -58.4},
    "geometry": {"PZE": {"H": 32.1, "zeta": 57.9, "psi": 12.4}},
    "selected_sources": [
      {"body": "Mars", "cost_J": 0.18, "confidence": 0.82}
    ]
  },
  "execution_mode": {
    "mode": "strict | robust",
    "resolution": "high | low",
    "reason": "string"
  },
  "axioms_active": ["4.3", "5.2", "9.3"],
  "question_type": "natal | relocation | temporal"
}
```

### C.3.2 Restricciones de Input
- El agente **debe asumir** que:
  - las posiciones son correctas,
  - las correcciones físicas ya fueron aplicadas,
  - el valor de $J$ es definitivo.
- El agente **no puede**:
  - solicitar recalcular posiciones,
  - alterar el sistema temporal,
  - ignorar el `execution_mode`.

---

## C.4 Interfaz de Salida (Output Contract)

### C.4.1 Principio General
- No devuelve texto libre.
- Devuelve **estructura semántica** separando juicio, confianza y alcance.

### C.4.2 Estructura Obligatoria de Output
```json
{
  "agent_id": "lilly_renaissance_v1",
  "school": "Renaissance/Lilly",
  "judgement": {
    "summary": "string",
    "claims": [
      {
        "statement": "string",
        "scope": "general | specific",
        "technique": "houses | signs | angles",
        "modality": "strong | moderated | weak"
      }
    ]
  },
  "confidence": {
    "global": 0.78,
    "by_source": [
      {"body": "Mars", "confidence": 0.82, "cost_J": 0.18}
    ]
  },
  "execution_notes": {
    "mode": "strict | robust",
    "limitations": ["Fine cusps disabled due to J threshold"]
  }
}
```

### C.4.3 Reglas de Confianza
- La **confianza global** es decreciente en $J$.
- Ningún claim puede ser “strong” si:
  - el agente está en **Modo Robusto**,
  - o la fuente tiene $J$ cercano a $J_{robust}$.

---

## C.5 Prohibiciones Explícitas
1. **Recalcular posiciones astronómicas** (Axioma 8.1)
2. **Contradecir el Modo de Ejecución**
   - En `mode = robust`: prohibido cúspides finas, divisionales, lenguaje determinista.
3. **Inferir causalidad física directa** (Axioma 9.3)
4. **Mezclar sistemas temporales** sin transformación provista por Abu.
5. **Omitir incertidumbre**: todo juicio debe declarar confianza.

---

## C.6 Manejo de Incertidumbre y Silencio

### C.6.1 Derecho al Silencio
Si $J > J_{robust}$ o input inválido, el agente **debe devolver**:
```json
{
  "judgement": null,
  "confidence": 0.0,
  "execution_notes": {
    "mode": "invalid",
    "reason": "Insufficient geometric robustness"
  }
}
```
El silencio es válido y preferible a una interpretación espuria.

---

## C.7 Compatibilidad y Versionado
- Todo agente debe declarar:
  - versión del contrato soportada,
  - escuela interpretativa,
  - supuestos geométricos.
- Agentes incompatibles **no pueden ser orquestados**.

---

## Cierre del Apéndice C
Este contrato garantiza:
- Interpretación subordinada a la geometría
- Incertidumbre explícita y cuantificada
- Sistema robusto ante ruido

El agente interpreta, pero **la ley la pone la axiomática**.

---

**Estado del Sistema:**
✔ Axiomas definidos  
✔ Backend especificado  
✔ Orquestador parametrizado  
✔ Agentes contractualmente contenidos

El sistema *Axiomatics of Heavens v0.3* queda **formalmente cerrado** a nivel arquitectónico.

---

*Fin del Apéndice C*
