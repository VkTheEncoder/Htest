import os
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from .anilist import search_anime
from .provider import MyLegalProvider
from .utils import pick_hd2_sub_source, highest_quality_from_m3u8, pick_english_sub

load_dotenv()
BOT_TOKEN   = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)
provider = MyLegalProvider()
application = Application.builder().updater(None).token(BOT_TOKEN).build()

@app.get("/")
def health(): return "OK", 200

@app.post(f"/{BOT_TOKEN}")
def tg_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

async def start(update: Update, _): await update.message.reply_text("Use /search <name>")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <anime name>")
        return
    q = " ".join(context.args)
    results = search_anime(q)
    if not results:
        await update.message.reply_text("No results.")
        return
    kb = [[InlineKeyboardButton(m["title"], callback_data=f"pick_anime:{m['id']}")] for m in results]
    await update.message.reply_text("Select a title:", reply_markup=InlineKeyboardMarkup(kb))

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("pick_anime:"):
        aid = int(data.split(":")[1])
        eps = provider.list_episodes(aid)
        kb = [[InlineKeyboardButton(f"Ep {e['number']}: {e.get('title','')}", callback_data=f"pick_ep:{e['ep_id']}")] for e in eps]
        kb.append([InlineKeyboardButton("⬇️ Download All (HD‑2 + EN)", callback_data=f"dl_all:{aid}")])
        await query.edit_message_text("Choose an episode:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("pick_ep:"):
        ep_id = data.split(":")[1]
        info = provider.get_episode_sources(ep_id)
        hd2 = pick_hd2_sub_source(info.get("sources", []))
        if not hd2:
            await query.edit_message_text("SUB: HD‑2 not available.")
            return
        try: best = highest_quality_from_m3u8(hd2)
        except Exception: best = hd2
        en = pick_english_sub(info.get("subtitles", []))
        await query.edit_message_text(f"• Video:\n{best}\n" + (f"• English subtitle:\n{en}" if en else "• English subtitle: not available"))
    elif data.startswith("dl_all:"):
        aid = int(data.split(":")[1])
        eps = provider.list_episodes(aid)
        lines = []
        for e in eps:
            info = provider.get_episode_sources(e["ep_id"])
            hd2 = pick_hd2_sub_source(info.get("sources", []))
            if not hd2: continue
            try: best = highest_quality_from_m3u8(hd2)
            except Exception: best = hd2
            en = pick_english_sub(info.get("subtitles", []))
            line = f"Ep {e['number']:>2}: {best}"
            if en: line += f"\n        Sub: {en}"
            lines.append(line)
        await query.edit_message_text("Download list:\n\n" + ("\n".join(lines) if lines else "No HD‑2 items."))

async def fallback(update: Update, _): await update.message.reply_text("Use /search <name>")

def register_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search_cmd))
    application.add_handler(CallbackQueryHandler(cb))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

def main():
    if not (BOT_TOKEN and WEBHOOK_URL):
        raise RuntimeError("BOT_TOKEN and WEBHOOK_URL required")
    register_handlers()
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))

if __name__ == "__main__":
    main()
