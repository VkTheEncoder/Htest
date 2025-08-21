import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from .anilist import search_anime
from .provider import MyLegalProvider
from .utils import pick_hd2_sub_source, highest_quality_from_m3u8, pick_english_sub

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
provider = MyLegalProvider()

async def start(update: Update, _):
    await update.message.reply_text("Use /search <name> to look up an anime (AniList).")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <anime name>")
        return
    q = " ".join(context.args).strip()
    try:
        results = search_anime(q)
    except Exception as e:
        await update.message.reply_text(f"Search failed: {e}")
        return
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
        if not eps:
            await query.edit_message_text("No episodes from provider.")
            return
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

        try:
            best = highest_quality_from_m3u8(hd2)
        except Exception:
            best = hd2

        en = pick_english_sub(info.get("subtitles", []))
        msg = f"• Video (SUB: HD‑2, highest):\n{best}\n"
        msg += f"• English subtitle:\n{en}" if en else "• English subtitle: not available"
        await query.edit_message_text(msg)

    elif data.startswith("dl_all:"):
        aid = int(data.split(":")[1])
        eps = provider.list_episodes(aid)
        lines = []
        for e in eps:
            info = provider.get_episode_sources(e["ep_id"])
            hd2 = pick_hd2_sub_source(info.get("sources", []))
            if not hd2: 
                continue
            try:
                best = highest_quality_from_m3u8(hd2)
            except Exception:
                best = hd2
            en = pick_english_sub(info.get("subtitles", []))
            line = f"Ep {e['number']:>2}: {best}"
            if en: line += f"\n        Sub: {en}"
            lines.append(line)
        await query.edit_message_text("Download list:\n\n" + ("\n".join(lines) if lines else "No HD‑2 items."))

async def fallback(update: Update, _):
    await update.message.reply_text("Use /search <name> to begin.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))
    app.run_polling()

if __name__ == "__main__":
    main()
