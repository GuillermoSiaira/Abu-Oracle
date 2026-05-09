from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import lilly_client
import subscriber_store


SUPPORTED_LANGS = ("es", "en", "fr", "pt")

MESSAGES = {
    "es": {
        "welcome": "Bienvenido a Abu Oracle. Elegi idioma y usa /sky, /calendar, /subscribe o /setbirth.",
        "subscribed": "Quedaste suscripto al parte mundano diario.",
        "unsubscribed": "Suscripcion pausada.",
        "sky_clear": "El cielo mundano no muestra configuraciones prioritarias ahora.",
        "sky_header": "Cielo mundano actual:",
        "calendar_empty": "No hay eventos mundanos mayores en los proximos 7 dias.",
        "calendar_header": "Proximos 7 dias:",
        "birth_usage": "Uso: /setbirth YYYY-MM-DD HH:MM Ciudad",
        "birth_saved": "Datos natales guardados. Usa /chart para preguntar a Lilly.",
        "no_birth": "Primero registra tus datos con /setbirth YYYY-MM-DD HH:MM Ciudad.",
        "ask_question": "Escribi tu pregunta para Lilly.",
        "language": "Idioma actualizado.",
        "error": "No pude completar la consulta ahora. Intenta de nuevo en unos minutos.",
    },
    "en": {
        "welcome": "Welcome to Abu Oracle. Choose a language and use /sky, /calendar, /subscribe, or /setbirth.",
        "subscribed": "You are subscribed to the daily mundane briefing.",
        "unsubscribed": "Subscription paused.",
        "sky_clear": "The mundane sky has no priority configurations right now.",
        "sky_header": "Current mundane sky:",
        "calendar_empty": "No major mundane events in the next 7 days.",
        "calendar_header": "Next 7 days:",
        "birth_usage": "Usage: /setbirth YYYY-MM-DD HH:MM City",
        "birth_saved": "Birth data saved. Use /chart to ask Lilly.",
        "no_birth": "Register your data first with /setbirth YYYY-MM-DD HH:MM City.",
        "ask_question": "Write your question for Lilly.",
        "language": "Language updated.",
        "error": "I could not complete the request now. Try again in a few minutes.",
    },
    "fr": {
        "welcome": "Bienvenue sur Abu Oracle. Choisis une langue et utilise /sky, /calendar, /subscribe ou /setbirth.",
        "subscribed": "Tu es abonne au bulletin quotidien.",
        "unsubscribed": "Abonnement suspendu.",
        "sky_clear": "Le ciel mondain ne montre pas de configuration prioritaire maintenant.",
        "sky_header": "Ciel mondain actuel :",
        "calendar_empty": "Aucun evenement majeur dans les 7 prochains jours.",
        "calendar_header": "Prochains 7 jours :",
        "birth_usage": "Usage : /setbirth YYYY-MM-DD HH:MM Ville",
        "birth_saved": "Donnees natales enregistrees. Utilise /chart pour interroger Lilly.",
        "no_birth": "Enregistre d'abord tes donnees avec /setbirth YYYY-MM-DD HH:MM Ville.",
        "ask_question": "Ecris ta question pour Lilly.",
        "language": "Langue mise a jour.",
        "error": "Je n'ai pas pu completer la demande. Reessaie dans quelques minutes.",
    },
    "pt": {
        "welcome": "Bem-vindo ao Abu Oracle. Escolhe um idioma e usa /sky, /calendar, /subscribe ou /setbirth.",
        "subscribed": "Voce foi inscrito no boletim mundano diario.",
        "unsubscribed": "Assinatura pausada.",
        "sky_clear": "O ceu mundano nao mostra configuracoes prioritarias agora.",
        "sky_header": "Ceu mundano atual:",
        "calendar_empty": "Nenhum evento mundano maior nos proximos 7 dias.",
        "calendar_header": "Proximos 7 dias:",
        "birth_usage": "Uso: /setbirth YYYY-MM-DD HH:MM Cidade",
        "birth_saved": "Dados natais salvos. Use /chart para perguntar a Lilly.",
        "no_birth": "Registre seus dados primeiro com /setbirth YYYY-MM-DD HH:MM Cidade.",
        "ask_question": "Escreva sua pergunta para Lilly.",
        "language": "Idioma atualizado.",
        "error": "Nao consegui completar a consulta agora. Tente novamente em alguns minutos.",
    },
}


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ES", callback_data="lang:es"),
            InlineKeyboardButton("EN", callback_data="lang:en"),
            InlineKeyboardButton("FR", callback_data="lang:fr"),
            InlineKeyboardButton("PT", callback_data="lang:pt"),
        ]
    ])


async def _lang(user_id: str) -> str:
    return await subscriber_store.get_lang(user_id) or "es"


def _msg(lang: str, key: str) -> str:
    return MESSAGES.get(lang, MESSAGES["es"]).get(key, MESSAGES["es"][key])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await subscriber_store.ensure_user(user_id)
    lang = await _lang(user_id)
    await update.message.reply_text(_msg(lang, "welcome"), reply_markup=_keyboard())


async def callback_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data or ""
    lang = data.split(":", 1)[1] if data.startswith("lang:") else "es"
    if lang not in SUPPORTED_LANGS:
        lang = "es"
    await subscriber_store.set_lang(user_id, lang)
    await query.edit_message_text(_msg(lang, "language"))


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.args and context.args[0].lower() in SUPPORTED_LANGS:
        lang = context.args[0].lower()
        await subscriber_store.set_lang(user_id, lang)
        await update.message.reply_text(_msg(lang, "language"))
        return
    await update.message.reply_text("ES / EN / FR / PT", reply_markup=_keyboard())


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    await subscriber_store.subscribe(user_id, lang=lang)
    await update.message.reply_text(_msg(lang, "subscribed"))


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    await subscriber_store.unsubscribe(user_id)
    await update.message.reply_text(_msg(lang, "unsubscribed"))


async def cmd_sky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    try:
        sky_data = await lilly_client.get_sky()
        configs = sky_data.get("active_configurations") or sky_data.get("configurations") or []
        if not configs:
            await update.message.reply_text(_msg(lang, "sky_clear"))
            return
        lines = []
        for config in configs[:3]:
            p_value = config.get("p_value")
            p_text = f"{p_value:.3f}" if isinstance(p_value, (int, float)) else "-"
            lines.append(f"- {config.get('label', config.get('type', 'config'))} (p={p_text})")
        await update.message.reply_text(_msg(lang, "sky_header") + "\n" + "\n".join(lines))
    except Exception:
        await update.message.reply_text(_msg(lang, "error"))


async def cmd_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    try:
        events = lilly_client.next_seven_days(await lilly_client.get_calendar(months=1))
        if not events:
            await update.message.reply_text(_msg(lang, "calendar_empty"))
            return
        lines = [
            f"- {event.get('date', '')}: {event.get('description', event.get('type', 'event'))}"
            for event in events[:8]
        ]
        await update.message.reply_text(_msg(lang, "calendar_header") + "\n" + "\n".join(lines))
    except Exception:
        await update.message.reply_text(_msg(lang, "error"))


async def cmd_setbirth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    raw = update.message.text or ""
    parts = raw.split(maxsplit=3)
    if len(parts) < 4:
        await update.message.reply_text(_msg(lang, "birth_usage"))
        return
    _, birth_date, birth_time, city = parts
    if len(birth_date) != 10 or len(birth_time) != 5:
        await update.message.reply_text(_msg(lang, "birth_usage"))
        return
    await subscriber_store.set_birth(
        user_id,
        {"birth_date": birth_date, "birth_time": birth_time, "birth_city": city},
    )
    await update.message.reply_text(_msg(lang, "birth_saved"))


async def cmd_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    birth = await subscriber_store.get_birth(user_id)
    if not birth:
        await update.message.reply_text(_msg(lang, "no_birth"))
        return
    context.user_data["awaiting_question"] = True
    await update.message.reply_text(_msg(lang, "ask_question"))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = await _lang(user_id)
    if not context.user_data.get("awaiting_question"):
        await update.message.reply_text(_msg(lang, "welcome"))
        return

    context.user_data["awaiting_question"] = False
    birth = await subscriber_store.get_birth(user_id)
    if not birth:
        await update.message.reply_text(_msg(lang, "no_birth"))
        return

    try:
        birth["telegram_user_id"] = user_id
        response = await lilly_client.ask_lilly(update.message.text or "", birth, lang)
        await update.message.reply_text(response[:4096])
    except Exception:
        await update.message.reply_text(_msg(lang, "error"))


async def format_daily_broadcast(lang: str) -> str:
    try:
        events = lilly_client.next_seven_days(await lilly_client.get_calendar(months=1))
        if events:
            event = events[0]
            return f"{_msg(lang, 'calendar_header')}\n{event.get('date', '')}: {event.get('description', event.get('type', 'event'))}"

        sky_data = await lilly_client.get_sky()
        configs = sky_data.get("active_configurations") or sky_data.get("configurations") or []
        if configs:
            config = configs[0]
            return f"{_msg(lang, 'sky_header')}\n{config.get('label', config.get('type', 'config'))}"
        return _msg(lang, "sky_clear")
    except Exception:
        return _msg(lang, "error")
