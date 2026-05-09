# TEL-C01 — Telegram Bot: Daily Mundana Broadcast + Chart Q&A

## Context

Abu Oracle needs a mobile-native distribution channel. The Telegram Bot serves two purposes:

1. **Daily broadcast** — subscribers receive the mundana insight automatically each morning
   (same content as the social posts, but personalized to the subscriber's language preference)
2. **Chart Q&A** — users can ask Lilly questions with their birth data on file

This is a Python service, deployed as a Cloud Run service (webhook mode) + Cloud Scheduler
for daily broadcasts.

## Architecture

```
Telegram servers
  → POST /webhook/{BOT_TOKEN}  (Cloud Run service: telegram-bot)
  → bot/handlers.py            → routes to command/message handlers
  → bot/lilly_client.py        → HTTP calls to Abu Engine + Lilly routes
  → Firestore                  → subscriber list + birth data

Cloud Scheduler (daily 08:05 UTC)
  → POST /broadcast            (same Cloud Run service, internal endpoint)
  → fetches current sky + calendar from Abu Engine
  → sends Telegram message to all subscribers
```

## Files to create

```
telegram_bot/
  main.py              — FastAPI app with /webhook and /broadcast endpoints
  handlers.py          — Command and message handlers
  lilly_client.py      — HTTP client for Abu Engine + Lilly routes
  subscriber_store.py  — Firestore CRUD for subscribers
  requirements.txt     — python-telegram-bot, fastapi, uvicorn, firebase-admin, requests
  Dockerfile
  cloudbuild-telegram-bot.yaml
```

## Spec

### Commands

| Command | Description |
|---|---|
| `/start` | Welcome + language selector inline keyboard |
| `/sky` | Current mundana sky (calls `GET /api/mundana/sky`) |
| `/calendar` | Next 7 days from calendar (calls `GET /api/mundana/calendar?months=1`) |
| `/subscribe` | Add user to daily broadcast list |
| `/unsubscribe` | Remove from broadcast list |
| `/chart` | Ask Lilly a question (requires birth data on file) |
| `/setbirth` | Register birth data: `YYYY-MM-DD HH:MM CityName` |
| `/language` | Change preferred language (ES/EN/FR/PT) |

### `main.py`

```python
from fastapi import FastAPI, Request, Header
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ABU_ENGINE_URL = os.environ.get("ABU_ENGINE_URL", "http://abu-engine:8000")
LILLY_URL = os.environ.get("LILLY_URL", "https://app.abu-oracle.com")

app = FastAPI()
bot_app = Application.builder().token(BOT_TOKEN).build()

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@app.post("/broadcast")
async def broadcast(request: Request, x_internal_secret: str = Header(None)):
    """Called by Cloud Scheduler daily. Sends mundana insight to all subscribers."""
    if x_internal_secret != os.environ.get("INTERNAL_SECRET"):
        return {"error": "unauthorized"}, 401
    await run_daily_broadcast()
    return {"ok": True}
```

### `handlers.py` — Key handlers

```python
async def cmd_sky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await subscriber_store.get_lang(user_id) or "es"
    sky_data = await lilly_client.get_sky()
    configs = sky_data.get("configurations", [])
    if not configs:
        text = MESSAGES[lang]["sky_clear"]
    else:
        lines = [f"• {c['label']} (p={c.get('p_value', '—'):.3f})" for c in configs[:3]]
        text = MESSAGES[lang]["sky_header"] + "\n" + "\n".join(lines)
    await update.message.reply_text(text)

async def cmd_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sends a free-text question; route to /api/chat with their birth data."""
    user_id = str(update.effective_user.id)
    birth = await subscriber_store.get_birth(user_id)
    if not birth:
        await update.message.reply_text(MESSAGES[lang]["no_birth"])
        return
    # Store the question; next message goes to Lilly
    context.user_data["awaiting_question"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_question"):
        context.user_data["awaiting_question"] = False
        question = update.message.text
        user_id = str(update.effective_user.id)
        birth = await subscriber_store.get_birth(user_id)
        lang = await subscriber_store.get_lang(user_id) or "es"
        response = await lilly_client.ask_lilly(question, birth, lang)
        await update.message.reply_text(response[:4096])  # Telegram max
```

### `subscriber_store.py` — Firestore schema

```
telegram_subscribers/{telegram_user_id}:
  lang: "es" | "en" | "fr" | "pt"
  subscribed: bool
  birth_date: "YYYY-MM-DD" | null
  birth_time: "HH:MM" | null
  birth_city: string | null
  birth_lat: float | null
  birth_lon: float | null
  created_at: ISO string
```

### `lilly_client.py` — Key calls

```python
import httpx

async def get_sky() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ABU_ENGINE_URL}/api/mundana/sky", timeout=15)
        return r.json()

async def get_calendar(months: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ABU_ENGINE_URL}/api/mundana/calendar", params={"months": months}, timeout=15)
        return r.json().get("events", [])

async def ask_lilly(question: str, birth: dict, lang: str) -> str:
    """
    POST to /api/chat with minimal birth context.
    Uses the Lilly API key (same as web app).
    """
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{LILLY_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": question}],
                "meta": {
                    "name": birth.get("name", ""),
                    "birthDate": birth.get("birth_date"),
                    "birthCity": birth.get("birth_city"),
                    "lat": birth.get("birth_lat"),
                    "lon": birth.get("birth_lon"),
                    "lang": lang,
                },
            },
            timeout=30,
            headers={"Authorization": f"Bearer {os.environ.get('LILLY_INTERNAL_TOKEN', '')}"},
        )
        return r.json().get("response", "—")
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### `requirements.txt`

```
python-telegram-bot==21.x
fastapi==0.115.x
uvicorn[standard]==0.30.x
httpx==0.27.x
firebase-admin==6.5.0
```

### Cloud Run + Scheduler setup (manual after deploy)

```bash
# Set webhook
curl https://api.telegram.org/bot{TOKEN}/setWebhook \
  -d "url=https://telegram-bot-xxx.run.app/webhook/{TOKEN}"

# Scheduler for daily broadcast
gcloud scheduler jobs create http telegram-daily-broadcast \
  --schedule="5 8 * * *" \
  --uri="https://telegram-bot-xxx.run.app/broadcast" \
  --message-body='{}' \
  --headers="X-Internal-Secret=${INTERNAL_SECRET},Content-Type=application/json" \
  --location=us-central1
```

### Required secrets (GCP Secret Manager)

```
telegram-bot-token           → TELEGRAM_BOT_TOKEN
telegram-internal-secret     → INTERNAL_SECRET
```

## Acceptance criteria

- [ ] `telegram_bot/main.py` defines FastAPI app with `/webhook/{TOKEN}` and `/broadcast` endpoints
- [ ] `/sky` command returns current sky configs from Abu Engine
- [ ] `/calendar` command returns next 7 days of mundana events
- [ ] `/subscribe` + `/unsubscribe` persist to Firestore
- [ ] `/setbirth YYYY-MM-DD HH:MM CityName` stores birth data in Firestore
- [ ] `/chart` + free text message triggers Lilly chat call and returns response
- [ ] `Dockerfile` builds and runs with `uvicorn main:app --host 0.0.0.0 --port 8080`
- [ ] `cloudbuild-telegram-bot.yaml` exists and follows same pattern as `cloudbuild-mundana-job.yaml`
- [ ] No Telegram tests required (mock-only); FastAPI endpoint unit tests optional

## Out of scope (future TEL-C02)

- Birth data auto-lookup from web app account (requires Firebase UID linking)
- Paid tier enforcement (Telegram users are free tier for now)
- Voice messages
- Inline keyboard for language/chart selection (text commands only for C01)
