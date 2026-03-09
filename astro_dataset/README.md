# Astro Dataset Scraper (carta-natal.es)

Pequeño submódulo para construir un dataset reproducible de datos natales desde carta-natal.es, dejando todo en formato JSONL para que Abu recalcule la carta y, más adelante, se derive el Harmony Field.

## Estructura

```
astro_dataset/
  data/
    raw/    # ids.csv, raw_birthdata.jsonl
    cache/  # HTML cache (pages, profiles)
  cartanatal/
    scraper.py  # cliente HTTP + crawler de IDs
    parser.py   # parser de fichas a BirthRecord
    models.py   # dataclass BirthRecord
  scripts/
    crawl_ids.py       # etapa 1: descubre ids → data/raw/ids.csv
    parse_profiles.py  # etapa 2: parsea fichas → data/raw/raw_birthdata.jsonl
    dataset_stats.py   # métricas rápidas del dataset
  tests/
```

## Dependencias

- Python 3.10+
- `requests`
- `beautifulsoup4`

Instalación rápida:

```bash
pip install requests beautifulsoup4
```

## Uso

1. Descubrir IDs (respeta 1 req/2s, cachea páginas):

```bash
python scripts/crawl_ids.py
```

2. Parsear fichas a JSONL (usa cache de perfiles, no re-solicita si existe):

```bash
python scripts/parse_profiles.py
```

Salida esperada:
- `data/raw/raw_birthdata.jsonl` — un registro por línea con solo datos natales y metadatos (hash HTML, timestamp, RR, scrape_source/version, etc.).

3. Métricas rápidas del dataset:

```bash
python scripts/dataset_stats.py
```

## Notas de diseño

- **Solo datos natales**: no se guardan posiciones, aspectos ni casas; Abu recalculará con sus efemérides.
- **Precisión temporal**: si no hay hora, `birth_time = null` y `time_precision = "unknown"`.
- **Rate limit**: mínimo 2 s entre requests; HTML cache en `data/cache/{pages|profiles}`.
- **Calidad**: separa luego dataset_gold (RR AA/A) vs dataset_full.
- **Reproducibilidad**: cada registro incluye `scrape_timestamp` (UTC), `scrape_source`, `scrape_version` y `html_hash` (sha256).

## Próximos pasos

- Añadir validaciones y tests de parsing con HTML guardado.
- Pipeline Abu → charts/vectores → HF (fuera del scope de este scraper).
