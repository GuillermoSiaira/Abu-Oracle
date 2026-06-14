FROM python:3.11-slim

WORKDIR /app
COPY telegram_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir google-cloud-firestore google-cloud-storage tweepy

COPY telegram_bot/ ./telegram_bot/
COPY scripts/mundana/publishers/ ./scripts/mundana/publishers/
RUN touch ./scripts/__init__.py ./scripts/mundana/__init__.py

ENV PYTHONPATH=/app

CMD ["uvicorn", "telegram_bot.main:app", "--host", "0.0.0.0", "--port", "8080"]
