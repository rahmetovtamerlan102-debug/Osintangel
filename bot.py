# bot.py
import os
import aiohttp
import logging
import urllib.parse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# ========== КОНФИГ ==========
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
PORT = int(os.getenv("PORT", 8081))

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден")
if not API_URL:
    raise ValueError("API_URL не найден")
if not API_KEY:
    raise ValueError("API_KEY не найден")

logging.basicConfig(level=logging.INFO, format='[SWILL] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== API ==========
async def api_request(endpoint: str, params: dict):
    params["api_key"] = API_KEY
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_URL}{endpoint}", params=params, timeout=60) as resp:
                return await resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

def format_person(p: dict) -> str:
    return (
        f"👤 {p.get('full_name', '—')}\n"
        f"📅 {p.get('birth_date', '—')}\n"
        f"📞 {p.get('phone', '—')}\n"
        f"🆔 ИНН: {p.get('inn', '—')}\n"
        f"🪪 Паспорт: {p.get('passport', '—')}\n"
        f"📍 {p.get('address', '—')}\n"
        f"🪪 СНИЛС: {p.get('snils', '—')}\n"
        f"📧 {p.get('email', '—')}"
    )

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 *FSSP PhoneBook Bot*\n\n"
        "Команды:\n"
        "/search_phone +71234567890\n"
        "/search_name Иванов\n"
        "/search_inn 910214822591\n"
        "/search_passport 1234567890\n"
        "/help — справка",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Справка*\n\n"
        "/search_phone +71234567890 — по номеру\n"
        "/search_name Иванов — по ФИО\n"
        "/search_inn 910214822591 — по ИНН\n"
        "/search_passport 1234567890 — по паспорту",
        parse_mode="Markdown"
    )

async def search_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /search_phone +71234567890")
        return
    phone = ''.join(filter(str.isdigit, context.args[0]))
    await update.message.reply_text(f"🔍 Ищу {phone}...")
    data = await api_request("/search/phone", {"phone": phone, "limit": 5})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    if data.get("total", 0) == 0:
        await update.message.reply_text("❌ Не найдено")
        return
    
    text = f"📞 *Найдено: {data['total']}*\n\n"
    for i, p in enumerate(data.get("results", [])[:5], 1):
        text += f"{i}. {format_person(p)}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /search_name Иванов")
        return
    name = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Ищу {name}...")
    data = await api_request("/search/name", {"name": urllib.parse.quote(name), "limit": 5})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    if data.get("total", 0) == 0:
        await update.message.reply_text("❌ Не найдено")
        return
    
    text = f"📝 *Найдено: {data['total']}*\n\n"
    for i, p in enumerate(data.get("results", [])[:5], 1):
        text += f"{i}. {format_person(p)}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def search_inn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /search_inn 910214822591")
        return
    inn = context.args[0]
    await update.message.reply_text(f"🔍 Ищу ИНН {inn}...")
    data = await api_request("/search/inn", {"inn": inn})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    if data.get("status") == "not_found":
        await update.message.reply_text("❌ Не найдено")
        return
    p = data.get("results", [{}])[0]
    await update.message.reply_text(f"🆔 *Найден*\n\n{format_person(p)}", parse_mode="Markdown")

async def search_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /search_passport 1234567890")
        return
    passport = context.args[0]
    await update.message.reply_text(f"🔍 Ищу паспорт {passport}...")
    data = await api_request("/search/passport", {"passport": passport})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    if data.get("status") == "not_found":
        await update.message.reply_text("❌ Не найдено")
        return
    p = data.get("results", [{}])[0]
    await update.message.reply_text(f"🪪 *Найден*\n\n{format_person(p)}", parse_mode="Markdown")

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("search_phone", search_phone))
    app.add_handler(CommandHandler("search_name", search_name))
    app.add_handler(CommandHandler("search_inn", search_inn))
    app.add_handler(CommandHandler("search_passport", search_passport))
    
    logger.info(f"🚀 Бот запущен на порту {PORT}")
    
    # Всегда используем polling (не нужен вебхук)
    app.run_polling()

if __name__ == "__main__":
    main()
