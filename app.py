import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
bot_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Bot działa. Twój chat ID: {update.effective_chat.id}\n"
        "Ustaw tę liczbę jako OWNER_CHAT_ID w Render."
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    if BOT_TOKEN:
        bot_app = Application.builder().token(BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
    yield
    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/send-photo")
async def send_photo(consent: str = Form(...), photo: UploadFile = File(...)):
    if consent != "yes":
        raise HTTPException(400, "Brak zgody.")
    if not bot_app or not OWNER_CHAT_ID:
        raise HTTPException(503, "Bot nie jest skonfigurowany.")
    if photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Wybierz plik JPG, PNG lub WEBP.")
    data = await photo.read()
    if not data or len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "Plik pusty lub większy niż 8 MB.")
    await bot_app.bot.send_photo(
        chat_id=int(OWNER_CHAT_ID),
        photo=data,
        caption="Zdjęcie wybrane i wysłane przez użytkownika za jego zgodą."
    )
    return {"sent": True}
