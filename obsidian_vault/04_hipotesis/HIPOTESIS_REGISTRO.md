---
name: HIPOTESIS_REGISTRO
description: Registro de hipótesis del proyecto — estado, evidencia y próximas pruebas
tipo: hipotesis
version: 2026-03-28
estado: activo
tags: [hipotesis, validacion, dominio, temporal, geografico, activacion]
---

# Registro de Hipótesis — Abu Oracle / HF

Ver también: [[HF_EXPERIMENT_LOG]] · [[domain_correlation_report]] · [[AXIOMATICS_v0_4]]

---

## H01 — Estructura Espacial del Campo HF

**Enunciado**: El Harmony Field define una estructura espacial no aleatoria sobre la superficie terrestre para cartas natales reales. Las cartas reales producen mayor RSI que rotaciones aleatorias de las mismas longitudes planetarias.

**Estado**: ✅ Confirmada (parcialmente)

**Evidencia**:
- Exp 1 ([[HF_EXPERIMENT_LOG#Experiment 1]]): mean z_RSI = 0.44, 33% de sujetos con z_RSI > 1
- Señal presente pero débil — formulación multiplicativa v2 no mejoró la señal

**Límite**: El RSI mide contraste relativo al natal, no correlación con eventos biográficos. La estructura espacial existe pero no garantiza validez predictiva.

**Próxima prueba**: Correlación HF(ubicación_del_evento) vs valence — requiere corpus GS_004-like con coordenadas por evento.

---

## H02 — Signos de los Pesos Harmony/Tension

**Enunciado**: Los aspectos armónicos (sextil, trígono) contribuyen positivamente al HF y los tensos (cuadratura, oposición) negativamente. La conjunción tiene el mayor peso positivo.

**Estado**: ⚠️ Parcialmente refutada — signos invertidos en producción

**Evidencia**:
- Grid search de 9,261 combinaciones sobre 527 eventos
- Pesos óptimos: w_harmony = −1.0, w_tension = −1.0, w_conjunction = +2.5
- Harmony y tension tienen el **mismo signo negativo** en el campo global

**Explicación**: El campo global mezcla eventos de distintas casas. La señal esperada se invierte porque el campo "escucha" todos los planetas simultáneamente — ver [[AXIOMATICS_v0_4#Axioma 8.1]].

**Hipótesis derivada (H02b)**: En el campo filtrado por dominio, el signo de harmony puede ser positivo. Aún no probado con suficientes datos.

---

## H03 — Especificidad de Dominio

**Enunciado**: El HF filtrado por los significadores de una casa predice mejor los eventos biográficos de esa casa que el HF global.

`corr(HF_dominio_k, eventos_k) > corr(HF_global, eventos_k)`

**Estado**: ✅ Confirmada en 3/6 dominios, no refutada en los 3 restantes

**Evidencia** (Exp 5, [[HF_EXPERIMENT_LOG#Experimento 5]]):

| Casa | Δcorr | delta_rb | Resultado |
|------|-------|----------|-----------|
| H04 | +0.306 | n/a | ✅ confirmado |
| H05 | +0.155 | n/a | ✅ confirmado |
| H06 | +0.369 | n/a | ✅ confirmado |
| H07 | −0.010 | +0.214 | neutro / señal en rb |
| H10 | −0.057 | +0.249 | Pearson limitado por N−=4 |

**Límite**: El corpus biográfico tiene sesgo sistemático hacia eventos positivos. N− insuficiente en H07 y H10 para Mann-Whitney.

---

## H04 — Hipótesis de Validación Espacial Directa

**Enunciado**: El delta HF entre la ubicación natal y la ubicación real del evento predice la valencia del evento — positivo donde el evento ocurrió implica HF_evento > HF_natal.

**Estado**: ❌ No probada (falta corpus con coordenadas por evento)

**Requisito**: Corpus con `lat/lon` por evento individual. Solo GS_004 (Siaira) tiene esto parcialmente, pero con baja movilidad geográfica — el test espacial queda vacío por construcción.

**Próxima prueba**: Construir corpus georeferenciado con sujetos de alta movilidad (músicos en gira, deportistas internacionales, diplomáticos).

---

## H05 — Firdaria como Filtro Temporal del HF

**Enunciado**: El campo de relocalización calculado con los planetas del período firdaria activo predice mejor la geografía de eventos del período que el campo global.

**Estado**: ❌ Pendiente de implementación

**Especificación técnica**:
```python
compute_relocation_field(
    reference_date=event.date,
    planet_subset=[firdaria_major, firdaria_minor]
)
```

**Fundamento**: Análogo a H03 pero en dimensión temporal. Si el subset de dominio filtra por *qué* (casa), el subset de firdaria filtra por *cuándo* (período activo).

---

## H06 — Convergencia Temporal como Amplificador

**Enunciado**: Cuando profección, firdaria y tránsito lento señalan el mismo período, la calidad de los eventos biográficos en ese período es significativamente mayor que en períodos con solo una técnica activa.

**Estado**: ❌ Pendiente de prueba sistemática

**Implementación actual**: `_detectConvergence()` en `context-builder.ts` — detecta la convergencia y la comunica a Lilly, pero no hay validación estadística sobre eventos biográficos.

**Próxima prueba**: Etiquetar períodos de convergencia en el corpus de 527 eventos y comparar valence_mean(convergencia) vs valence_mean(no_convergencia).

---

## H07 — HF × Tránsito × Fecha

**Enunciado**: La combinación de HF_dominio alto en una ubicación + tránsito favorable activo en una fecha específica tiene mayor correlación con eventos positivos que cualquiera de los dos factores por separado.

**Estado**: ❌ Especulativa — no modelada aún

**Descripción**: "Ve a esta ciudad en este mes para este propósito." La interacción HF(lugar) × tránsito(tiempo) × dominio(propósito) es el producto completo de relocalización.

**Fundamento axiomático**: [[AXIOMATICS_v0_4#Axioma 9.4]] — la manifestación completa requiere potencial natal + resonancia geográfica + activación temporal.

---

## H08 — Ontología del Campo Continuo (hipótesis del mecanismo)

**Enunciado**: La geometría planetaria correlaciona con experiencia biográfica porque ambas son
geometrías del mismo campo continuo. La luz es modulación del campo EM, no entidad separada.
El horizonte local es el operador que define qué región del campo es localmente dominante para
una configuración de individuación específica.

**Estado**: ❌ Hipótesis especulativa — falsable, no probada

**Evidencia consistente (no probatoria):**
- HF_v6 Cohen's d H10=+0.702 — señal estadística existente
- El sistema ya implementa el invariante natal ($\Delta_{natal}$) sin nombrarlo explícitamente

**Consecuencia si verdadera:** elimina el problema filosófico de la acción a distancia.
No hay "influencia que viaja" — hay geometría del mismo campo.

**Próxima prueba**: formalización en Axiomática v0.5 + publicación como paper 3 páginas.

Documento completo: [[AXIOM_0_MECANISMO]]

---

## H09 — Código Dual del Nativo

**Enunciado**: El evento de individuación imprime dos códigos simultáneos sobre el mismo campo:
$\mathcal{I}_{nativo} = \{\pi_{natal}, \mathcal{N}\}$. El código nominal $\mathcal{N}$
opera sobre el mismo campo que el código celeste. La transformación $T(\mathcal{N}) \to \mathbb{Z}
\to \text{geometría}$ existe en el corpus hermético (gematría).

**Estado**: ❌ Especulativa — horizonte futuro Abu Oracle

**Consecuencia de diseño:** agente hermético en Lilly Swarm (Lilly Swarm v2.0) que opera
sobre $\mathcal{N}$ con su propia métrica de decodificación.

**Fuente doctrinal**: Hermes Trismegisto → Plotino → Proclo → Ficino. Gematría como
métrica formal.

Documento completo: [[AXIOM_0_MECANISMO]]

---

## H_mundana_A — Conjunciones de ciclo largo como marcadores epocales

**Enunciado**: Las configuraciones planetarias de ciclo largo (conjunciones Júpiter-Saturno, oposiciones Marte-Saturno) presentan, alrededor de su fecha exacta, una densidad de eventos históricos significativamente superior al ruido de fondo del corpus.

**Estado**: ✅ Confirmada — robusta para J-S, señal real para M-S

**Evidencia** (corpus 23.636 eventos, año 8–2069):

| Configuración | p-value | r (rank-biserial) | Densidad |
|---|---|---|---|
| Conjunción Júpiter-Saturno | 5×10⁻⁶ | +0.204 | 4.3× baseline |
| Oposición Marte-Saturno | 0.016 | +0.056 | 1.6× baseline |

**Hallazgo clave J-S:** 8.67 eventos/ventana vs 2.02 baseline. Confirma doctrina Abu Mashar.

**Limitación:** corpus sesgado siglo XIX-XX (68% eventos). Réplica estratificada por siglo es el siguiente paso.

**Fuente doctrinal**: Abu Mashar al-Balkhi, *De Magnis Coniunctionibus* (siglo IX). Las conjunciones J-S como marcadores de transiciones políticas, religiosas y culturales mayores.

**Fundamento axiomático**: [[AXIOMATICS_v0_4#11. Principio de Estratificación de Niveles Operativos]] — Axiomas 11.1, 11.2, 11.3.

**Implementación**: [[MUNDANA_PHASE12]] — módulo `abu_engine/core/mundana.py` + publisher Cloud Run.

**Documento completo**: [[MUNDANA_H_A_RESULTADOS]]

---

## H_v6 — Dignidad como modulador de angularidad + intersección firdaria∩dominio

**Enunciado:** Angularidad × dignity_score × w_intersección produce
mayor d que HF_v3 en dominios específicos.

**Test:** Correlador sobre 529 eventos, 26 sujetos, 4 dominios.

**Resultado:**
- H07 d=+0.587 (vs +0.055 en v3) — efecto medio-grande
- H10 d=+0.702 (vs +0.056 en v3) — efecto grande

**Estado:** ✅ Confirmada — no falsada. Señal fuerte en 2 dominios.

**Fuente:** [[HF_V6_RESULTS]]

**Doctrinal:** [[AXIOMATICS_v0_4]] Axiomas 8 y 9

**Implementación:** [[hf_v6]]
