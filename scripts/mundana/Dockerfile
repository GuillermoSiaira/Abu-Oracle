FROM python:3.11-slim

WORKDIR /app

# Sistema: swisseph necesita build tools solo en compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libssl-dev \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements-mundana.txt .
RUN pip install --no-cache-dir -r requirements-mundana.txt

# Código fuente del publisher
COPY scripts/mundana/ ./mundana/

# data/mundana/{drafts,registry,logs} se crean en runtime por el pipeline

WORKDIR /app/mundana

# Moshier fallback — pyswisseph no necesita archivos de ephemerides externos
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

CMD ["python", "main_publisher.py"]
