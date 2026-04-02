# AI Oracle — Session Log: Fase 2 Frontend + Demo Hi-Res (2026-03-09/10)

## Resumen
Implementación completa de la ruta `/relocation` en el frontend Next.js y regeneración del demo pack a mayor resolución con rankings deduplicados.

## Cambios realizados

### Archivos creados
| Archivo | Descripción |
|---------|-------------|
| `next_app/app/relocation/page.tsx` | Server component con Suspense |
| `next_app/app/relocation/RelocationClient.tsx` | Client principal: dropdown sujeto, selector idioma (es/en/pt/fr), mapa, tabla, narrativa |
| `next_app/components/NarrativePanel.tsx` | Panel de narrativa con markdown + acciones |
| `next_app/components/RankingTable.tsx` | Tabla top-20 con Δ natal, iconos, colores |
| `scripts/regenerate_demo_hires.py` | Script de regeneración de demo pack a resolución configurable (--step) |

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `next_app/components/Navigation.tsx` | Barra de navegación con links (Home, Carta, Relocalización) + active state |
| `next_app/components/chart-tabs.tsx` | Tab "Relocation" → "Mi Relocalización" con placeholder para endpoint personal |
| `next_app/package.json` | react-markdown 8→9, remark-gfm 3→4 (fix TS5 build error) |
| `next_app/public/demo/` | Demo data copiado y sincronizado (10 sujetos) |

### Datos regenerados
- **Grid**: 5° (2,409 pts, ~480KB) → **2.5° (9,425 pts, ~1.8MB)** por sujeto
- **Rankings**: deduplicados por ciudad (best HF per unique city, 20 ciudades únicas)
- **Tiempo de cómputo**: 103 segundos para 10 sujetos
- **Entorno**: requiere `venv310` (tiene pyswisseph + pyarrow)

### Dependencias instaladas en venv310
- `pyarrow` (para lectura de parquets)

## Problemas encontrados y resueltos
1. **react-markdown@8 + TS5**: `Cannot find namespace 'JSX'` → upgrade a v9
2. **pyswisseph**: no disponible en Python global, sí en venv310
3. **pip launcher roto en venv310**: usar `python -m pip` en vez de `pip` directamente
4. **Rankings duplicados**: múltiples grid points mapeaban a la misma ciudad → dedup por ciudad

## Estado actual del frontend
```
Route                    Size      First Load JS
/                        3.03 kB   103 kB
/chart                   7.66 kB   107 kB
/relocation              48.7 kB   148 kB
/relocation-map          210 kB    310 kB (legacy, obsoleta)
```

## Pendiente
1. Regenerar narrativas con Lilly real (requiere servicio corriendo)
2. Fase 3: Endpoint Abu `GET /api/astro/relocation`
3. Conectar tab "Mi Relocalización" en /chart al endpoint live
4. Considerar eliminar ruta `/relocation-map` (legacy, reemplazada por `/relocation`)
