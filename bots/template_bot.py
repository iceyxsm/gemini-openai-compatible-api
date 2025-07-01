import os
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = os.getenv("BOT_ID")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/v1/chat/completions")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Fetch API key and base prompt for this bot
def get_api_key_and_prompt():
    bot = supabase.table("bots").select("api_key_id, base_prompt").eq("id", BOT_ID).single().execute()
    if not hasattr(bot, 'data') or not bot.data:
        return None, None
    api_key_id = bot.data["api_key_id"]
    base_prompt = bot.data["base_prompt"]
    key_row = supabase.table("user_api_keys").select("key").eq("id", api_key_id).single().execute()
    api_key = key_row.data["key"] if hasattr(key_row, 'data') and key_row.data else None
    return api_key, base_prompt

API_KEY, BASE_PROMPT = get_api_key_and_prompt()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    messages = []
    if BASE_PROMPT:
        messages.append({"role": "user", "content": BASE_PROMPT})
    messages.append({"role": "user", "content": user_message})
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    try:
        resp = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=30)
        data = resp.json()
        if resp.status_code == 200:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = data.get("error", {}).get("message", "API error")
    except Exception as e:
        reply = f"Error: {e}"
    await update.message.reply_text(reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me a message and I'll reply using Gemini.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling() 