FROM python:3.11-slim

WORKDIR /app

# Sistema: swisseph necesita build tools solo en compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements-mundana.txt .
RUN pip install --no-cache-dir -r requirements-mundana.txt

# Código fuente del publisher
COPY scripts/mundana/ ./mundana/

# data/mundana/{drafts,registry,logs} se crean en runtime por el pipeline

# Ephemerides Swiss Ephemeris (compartidas con abu_engine)
# Si no están disponibles, pyswisseph usa Moshier como fallback
COPY abu_engine/ephe/ ./ephe/

WORKDIR /app/mundana

# Configuración de ephemerides y encoding
ENV SWISSEPH_PATH=/app/ephe
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

CMD ["python", "main_publisher.py"]
