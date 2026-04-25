---
name: 00_dashboard
description: Dashboard vivo del proyecto — estado de hipótesis, experimentos y validación
tipo: dashboard
tags: [dashboard, index]
---

# Abu Oracle — Dashboard

> Generado dinámicamente por Dataview. Refresca automáticamente al abrir.

---

## Hipótesis — Estado

```dataview
TABLE estado, tags
FROM "04_hipotesis"
WHERE tipo = "hipotesis" AND file.name != "HIPOTESIS_REGISTRO"
SORT estado ASC
```

---

## Hipótesis confirmadas ✅

```dataview
TABLE file.link AS Hipótesis, estado
FROM "04_hipotesis"
WHERE contains(estado, "✅")
SORT file.name ASC
```

---

## Resultados — Documentos activos

```dataview
TABLE estado, version
FROM "05_resultados"
WHERE tipo = "resultado" OR tipo = "resultados" OR tipo = "revision" OR tipo = "corpus"
SORT version DESC
```

---

## Experimentos — Blind Validation

```dataview
TABLE status, score_summary, rodden
FROM "03_experimentos"
WHERE contains(tags, "blind_validation")
SORT file.name ASC
```

---

## Engineering — Módulos en producción

```dataview
TABLE estado, version
FROM "06_engineering"
WHERE contains(estado, "producción") OR contains(estado, "✅")
SORT file.mtime DESC
```

---

## Doctrina — Versiones activas

```dataview
TABLE version, estado
FROM "02_doctrina"
WHERE estado = "activo"
SORT version DESC
```

---

## Todos los documentos por tipo

```dataview
TABLE tipo, estado
FROM ""
WHERE tipo != null AND file.name != "00_dashboard" AND file.name != "00_index"
SORT tipo ASC, file.name ASC
```
