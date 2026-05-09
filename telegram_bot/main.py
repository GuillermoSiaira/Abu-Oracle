from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import handlers
import subscriber_store


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "")

app = FastAPI(title="Abu Oracle Telegram Bot")
bot_app = Application.builder().token(BOT_TOKEN).build()


bot_app.add_handler(CommandHandler("start", handlers.cmd_start))
bot_app.add_handler(CommandHandler("sky", handlers.cmd_sky))
bot_app.add_handler(CommandHandler("calendar", handlers.cmd_calendar))
bot_app.add_handler(CommandHandler("subscribe", handlers.cmd_subscribe))
bot_app.add_handler(CommandHandler("unsubscribe", handlers.cmd_unsubscribe))
bot_app.add_handler(CommandHandler("chart", handlers.cmd_chart))
bot_app.add_handler(CommandHandler("setbirth", handlers.cmd_setbirth))
bot_app.add_handler(CommandHandler("language", handlers.cmd_language))
bot_app.add_handler(CallbackQueryHandler(handlers.callback_language, pattern=r"^lang:"))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))


@app.on_event("startup")
async def startup() -> None:
    await bot_app.initialize()
    await bot_app.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await bot_app.stop()
    await bot_app.shutdown()


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


async def run_daily_broadcast() -> dict:
    subscribers = await subscriber_store.list_subscribers()
    sent = 0
    failed = 0
    cache: dict[str, str] = {}

    for subscriber in subscribers:
        chat_id = subscriber["telegram_user_id"]
        lang = subscriber.get("lang") or "es"
        if lang not in cache:
            cache[lang] = await handlers.format_daily_broadcast(lang)
        try:
            await bot_app.bot.send_message(chat_id=chat_id, text=cache[lang][:4096])
            sent += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "subscribers": len(subscribers)}


@app.post("/broadcast")
async def broadcast(x_internal_secret: str | None = Header(default=None)):
    if not INTERNAL_SECRET or x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")
    result = await run_daily_broadcast()
    return {"ok": True, **result}
