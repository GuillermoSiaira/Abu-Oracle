# PIPELINE_LAUNCH_CHECKLIST

Checklist operativo para encender el pipeline batch (Abu → Storacha/IPFS → Vercel) — 2026-03-03.

## 1) Datos y esquema
- [ ] Curar lista de subjects/eventos (UTC, lat/lon, fuente/licencia, precisión de hora)
- [ ] Definir schema de artifacts (JSON/CSV) con campos obligatorios: subject_id, birth_datetime_utc, lat, lon, chart, aspects, transits (opcional), metadata (license, precision_flag)
- [ ] Documentar intended use/licencia (CC0/CC-BY) en cada artifact

## 2) Infra y secrets
- [ ] DB provisionada (Postgres/SQLite hosted) con tablas `subjects`, `runs`, `artifacts`
- [ ] Migraciones aplicadas
- [ ] Secret Manager: keys Storacha/IPFS, Abu URL, DB URL, API key opcional
- [ ] Imagen del pipeline (Cloud Run Job) con Abu client + uploader Storacha; incluye `de440s.bsp` y tzdata

## 3) Abu / API
- [ ] Abu desplegado (Cloud Run service o contenedor local en el Job)
- [ ] Endpoints validados: `/api/astro/chart(-detailed)`, `/forecast`, `/life-cycles`, `/solar-return`, `/astro/transits` y `/astro/transits/with-natal`
- [ ] Casas: fallback a Whole Sign en latitudes altas verificado
- [ ] Tránsitos: velocidades y `includeMinor` probados

## 4) Pipeline y Scheduler
- [ ] Cloud Run Job configurado con envs/secrets
- [ ] Payload de subjects/rango de fechas definido
- [ ] Cloud Scheduler (cron) apuntando al Job con retries/alertas básicas
- [ ] Logging estructurado con `run_id`; logs accesibles

## 5) Storage y publicación
- [ ] Upload a Storacha/IPFS funcionando (CID + checksum)
- [ ] Guardar CIDs en `artifacts` y generar index público (JSON) para agentes/landing
- [ ] Landing en Vercel leyendo el index/CIDs y enlazando artifacts

## 6) Validación
- [ ] Run manual de prueba (lote pequeño) → verificar artifacts, CIDs, landing
- [ ] Tiempo/latencias registradas; costos estimados
- [ ] Revisar licencias y uso aceptable (AUP) antes de abrir al público

## 7) Comunicaciones
- [ ] README breve de consumo para agentes/LLMs (endpoints/index, campos, licencia)
- [ ] Changelog interno con versiones de la imagen del Job
