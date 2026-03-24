
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Download de440s.bsp (32 MB Skyfield ephemeris) at build time.
# weights.json and cities.json live in abu_engine/ root and are copied by COPY . .
RUN mkdir -p /app/data && \
    python -c "from skyfield.api import Loader; load = Loader('/app/data'); load('de440s.bsp')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

