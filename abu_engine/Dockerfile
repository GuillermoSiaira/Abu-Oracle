
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Download Skyfield ephemeris at build time so the image is self-contained.
# The file is gitignored (data/ in root .gitignore) and therefore absent from
# Cloud Build source archives; baking it into the image avoids runtime download failures.
RUN mkdir -p /app/data && \
    python -c "from skyfield.api import Loader; load = Loader('/app/data'); load('de440s.bsp')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

