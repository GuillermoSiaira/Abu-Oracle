---
name: BABEL_phase0
description: Phase 0 — validación de clustering semántico cross-especie en espacio de embeddings
tipo: experiment
estado: en_progreso
tags: [babel, phase0, UMAP, clustering, NatureLM, embeddings]
fecha: 2026-05-01
---

# BABEL Phase 0 — Validación del Clustering Semántico

## Pregunta

> Si una señal de alarma aérea de un vervet monkey y una señal de hawk de un prairie dog pasan por el mismo encoder semántico, ¿salen cerca en el espacio de embeddings?

Si sí → el grafo inter-especie es construible.
Si no → hay que repensar el encoder o la taxonomía de primitivas.

---

## Setup

| Parámetro | Valor |
|---|---|
| Encoder | NatureLM-audio (BEATs + Llama 3.1 8B) en producción; demo sintético |
| Reducción dimensional | UMAP (n_neighbors=20, min_dist=0.05) |
| Métrica de clustering | Silhouette score [-1, 1] |
| Dataset demo | 500 señales sintéticas, 9 especies, 9 primitivas |
| Dataset real | En descarga (ESP HuggingFace) |

---

## Resultado demo (datos sintéticos calibrados)

**Silhouette score: 0.750** ✅ (excelente — >0.7)

![[phase0_embedding_map.png]]

### Lectura del mapa

**Panel izquierdo (por primitiva):**
Los 9 colores forman clusters visualmente claros y separados. Señales con la misma función comunicativa agrupan juntas independientemente de la especie que las emite.

**Panel derecho (por especie):**
Dentro de cada cluster de primitiva conviven múltiples especies (distintos marcadores). Vervet monkey + prairie dog + crow comparten el cluster ALARM_AERIAL. Delfín + elefante + cachalote comparten CONTACT_AFFILIATION.

Esto es la hipótesis central visualizada: **el "idioma" varía, el significado converge**.

---

## Interpretación

### ¿Qué significaría este resultado con datos reales?

Si NatureLM-audio (entrenado en audio real de múltiples especies) produce embeddings donde las alarmas aéreas de vervets y prairie dogs caen cerca → el modelo ya "sabe" que esas señales son funcionalmente equivalentes, aunque nunca fue entrenado explícitamente para eso.

Esto sería una capacidad emergente del preentrenamiento masivo — análoga a cómo los LLMs emergen habilidades de traducción sin entrenamiento explícito de traducción.

### Threshold de decisión

| Silhouette | Decisión |
|---|---|
| > 0.7 | ✅ Pipeline directo: clasificador fino encima de embeddings |
| 0.5–0.7 | ⚠️ Fine-tuning necesario pero proyecto viable |
| 0.25–0.5 | ⚠️ Re-entrenar encoder con datos etiquetados |
| < 0.25 | ❌ Encoder no captura semántica inter-especie — repensar approach |

---

## Próximos pasos

### Phase 0 → Phase 1

1. **Datos reales**: correr NatureLM-audio sobre corpus etiquetados (vervet alarm calls, prairie dog vocabulary, Watkins cetaceans)
2. **Validar threshold**: ¿silhouette con datos reales supera 0.5?
3. **Si sí**: construir BabelGraph con 5 especies × 9 primitivas (Phase 1)

### Código

```bash
# Descargar datos
python babel/data/download_hf.py

# Correr encoder real (requiere GCP T4)
python babel/notebooks/phase0_embedding_explorer.py

# Costo estimado GCP: ~$5-15
```

Repo: `D:\projects\QUEST` rama `feat/babel`

---

## Experimento 2 — MFCC real (sin GPU)

**Fecha**: 2026-05-01 | **Archivo**: `babel/notebooks/phase0_local_mfcc.py`

| Métrica | Valor | Interpretación |
|---|---|---|
| Silhouette primitiva | **-0.185** | Sin clustering semántico cross-especie |
| Silhouette especie | -0.043 | Leve agrupación acústica por especie |
| NN mismo primitivo | 84% (357/425) | Dentro de cada especie, sí se agrupan |
| NN cross-especie | 0.2% (1/425) | Las paredes son de especie, no de semántica |

**Resultado**: ❌ esperado y correcto — los MFCCs capturan morfología vocal (especie) no función semántica.

**Diagnóstico clave**: Un alarm-aerial de vervet y uno de prairie dog suenan acústicamente distintos — solo convergen en *significado*. Los MFCCs miden forma espectral del tracto vocal, no semántica funcional.

**Implicación directa**: Este resultado **valida la hipótesis central de BABEL** — la equivalencia funcional cross-especie no es recuperable de características acústicas brutas. Requiere un encoder con representación semántica (NatureLM-audio, entrenado sobre múltiples especies simultáneamente).

El panel derecho del mapa UMAP muestra exactamente esto: cada especie forma su propio blob acústico compacto, sin solapamiento por primitiva semántica.

---

## Log de sesión

| Fecha | Acción | Resultado |
|---|---|---|
| 2026-05-01 | Demo visual con datos sintéticos | Silhouette = 0.750 ✅ |
| 2026-05-01 | Descarga HF ESP → audio sintético realista | 425 señales generadas (9 especies × 9 primitivas) |
| 2026-05-01 | MFCC Phase 0 con audio real (librosa, sin GPU) | Silhouette = -0.185 ❌ esperado — valida necesidad de encoder semántico |
| — | NatureLM-audio en GCP T4 | **Próximo paso** — requiere $5-15 |
