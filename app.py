import os
import asyncio
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from data import DARS_JADVALI, OQUVCHILAR, USTOZLAR

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.environ.get("PORT", 8000))

async def start(update: Update, context):
    keyboard = [["📚 Dars jadvali", "👨‍🏫 Ustozlar"], ["👥 O'quvchilar", "ℹ️ Bot haqida"]]
    await update.message.reply_text(
        "🏫 *9-B ixtisoslashgan sinf botiga xush kelibsiz!*",
        parse_mode="Markdown",
        reply_markup={"keyboard": keyboard, "resize_keyboard": True}
    )

async def dars_jadvali(update: Update, context):
    keyboard = [["Dushanba", "Seshanba"], ["Chorshanba", "Payshanba"], ["Juma", "Shanba"], ["🔙 Asosiy menyu"]]
    await update.message.reply_text("📅 *Kun tanlang:*", parse_mode="Markdown", reply_markup={"keyboard": keyboard, "resize_keyboard": True})

async def show_jadval(update: Update, context):
    kun = update.message.text
    darslar = DARS_JADVALI.get(kun, [])
    if not darslar:
        await update.message.reply_text("❌ Ma'lumot topilmadi!")
        return
    text = f"📅 *{kun} kungi dars jadvali:*\n\n" + "\n".join([f"📖 {d}" for d in darslar])
    await update.message.reply_text(text, parse_mode="Markdown")

async def ustozlar(update: Update, context):
    fanlar = list(USTOZLAR.keys())
    keyboard = [[fanlar[i], fanlar[i+1]] if i+1 < len(fanlar) else [fanlar[i]] for i in range(0, len(fanlar), 2)]
    keyboard.append(["🔙 Asosiy menyu"])
    await update.message.reply_text("👨‍🏫 *Fan tanlang:*", parse_mode="Markdown", reply_markup={"keyboard": keyboard, "resize_keyboard": True})

async def show_ustoz(update: Update, context):
    fan = update.message.text
    m = USTOZLAR.get(fan)
    if not m:
        await update.message.reply_text("❌ Ma'lumot topilmadi!")
        return
    text = f"👨‍🏫 *{m['ism']}*\n📖 *Fani:* {fan}\nℹ️ {m['tavsif']}"
    if m.get("sinf_rahbari"):
        text += "\n\n⭐ *Sinf rahbaringiz!* ⭐"
    await update.message.reply_text(text, parse_mode="Markdown")

async def oquvchilar(update: Update, context):
    names = list(OQUVCHILAR.keys())
    keyboard = [[names[i], names[i+1]] if i+1 < len(names) else [names[i]] for i in range(0, len(names), 2)]
    keyboard.append(["🔙 Asosiy menyu"])
    await update.message.reply_text("👥 *O'quvchi tanlang:*", parse_mode="Markdown", reply_markup={"keyboard": keyboard, "resize_keyboard": True})

async def show_oquvchi(update: Update, context):
    ism = update.message.text
    m = OQUVCHILAR.get(ism)
    if not m:
        await update.message.reply_text("❌ Ma'lumot topilmadi!")
        return
    await update.message.reply_text(f"👤 *{ism}*\n\nℹ️ {m['tavsif']}", parse_mode="Markdown")

async def bot_haqida(update: Update, context):
    await update.message.reply_text("🤖 *9-B sinf boti*\n\n✅ Dars jadvali\n✅ Ustozlar\n✅ O'quvchilar", parse_mode="Markdown")

async def back_to_main(update: Update, context):
    keyboard = [["📚 Dars jadvali", "👨‍🏫 Ustozlar"], ["👥 O'quvchilar", "ℹ️ Bot haqida"]]
    await update.message.reply_text("🏫 *Asosiy menyu:*", parse_mode="Markdown", reply_markup={"keyboard": keyboard, "resize_keyboard": True})

async def handle_message(update: Update, context):
    text = update.message.text
    if text == "📚 Dars jadvali":
        await dars_jadvali(update, context)
    elif text == "👨‍🏫 Ustozlar":
        await ustozlar(update, context)
    elif text == "👥 O'quvchilar":
        await oquvchilar(update, context)
    elif text == "ℹ️ Bot haqida":
        await bot_haqida(update, context)
    elif text == "🔙 Asosiy menyu":
        await back_to_main(update, context)
    elif text in ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]:
        await show_jadval(update, context)
    elif text in USTOZLAR:
        await show_ustoz(update, context)
    elif text in OQUVCHILAR:
        await show_oquvchi(update, context)
    else:
        await update.message.reply_text("❓ Menyu tugmalaridan foydalaning!")

async def main():
    application = Application.builder().token(TOKEN).updater(None).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        await application.bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
    
    async def webhook(request: Request):
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response()
    
    async def health(request: Request):
        return PlainTextResponse("OK")
    
    starlette_app = Starlette(routes=[
        Route("/webhook", webhook, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ])
    
    import uvicorn
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())