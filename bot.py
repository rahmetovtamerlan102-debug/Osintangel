# bot.py
import os
import aiohttp
import logging
import urllib.parse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загрузка .env
load_dotenv()

# ========== КОНФИГ ==========
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
PORT = int(os.getenv("PORT", 8081))

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")
if not API_URL:
    raise ValueError("API_URL не найден в .env")
if not API_KEY:
    raise ValueError("API_KEY не найден в .env")

logging.basicConfig(
    level=logging.INFO,
    format='[SWILL] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== API ЗАПРОСЫ ==========
async def api_request(endpoint: str, params: dict):
    """Запрос к FSSP API"""
    params["api_key"] = API_KEY
    url = f"{API_URL}{endpoint}"
    logger.info(f"Запрос к API: {url}?{params}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=60) as resp:
                return await resp.json()
        except Exception as e:
            logger.error(f"API ошибка: {e}")
            return {"status": "error", "error": str(e)}

def format_person(person: dict, index: int = 0) -> str:
    """Форматирует одну запись"""
    text = f"👤 *{person.get('full_name', '—')}*\n"
    text += f"📅 Дата рождения: {person.get('birth_date', '—')}\n"
    text += f"📞 Телефон: {person.get('phone', '—')}\n"
    text += f"🆔 ИНН: {person.get('inn', '—')}\n"
    text += f"🪪 Паспорт: {person.get('passport', '—')}\n"
    text += f"📍 Адрес: {person.get('address', '—')}\n"
    text += f"🪪 СНИЛС: {person.get('snils', '—')}\n"
    text += f"📧 Email: {person.get('email', '—')}"
    return text

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 *FSSP PhoneBook Bot*\n\n"
        "Ищу людей по базе ФССП (67 млн записей)\n\n"
        "Команды:\n"
        "/search_phone +71234567890 — по телефону\n"
        "/search_name Иванов — по ФИО\n"
        "/search_inn 910214822591 — по ИНН\n"
        "/search_passport 1234567890 — по паспорту\n"
        "/help — справка\n\n"
        "⚡️ Данные из открытых источников",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Справка*\n\n"
        "1. Поиск по номеру телефона:\n"
        "`/search_phone +71234567890`\n\n"
        "2. Поиск по ФИО:\n"
        "`/search_name Иванов`\n\n"
        "3. Поиск по ИНН:\n"
        "`/search_inn 910214822591`\n\n"
        "4. Поиск по паспорту:\n"
        "`/search_passport 1234567890`\n\n"
        "📌 Формат номера: 71234567890 или +71234567890",
        parse_mode="Markdown"
    )

async def search_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по номеру телефона"""
    if not context.args:
        await update.message.reply_text("❌ Укажите номер: `/search_phone +71234567890`", parse_mode="Markdown")
        return
    
    phone = ''.join(filter(str.isdigit, context.args[0]))
    await update.message.reply_text(f"🔍 Поиск по номеру: {phone}...")
    
    data = await api_request("/search/phone", {"phone": phone, "limit": 5})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    
    total = data.get("total", 0)
    if total == 0:
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    text = f"📞 *Найдено: {total} записей*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, person in enumerate(data.get("results", [])[:5], 1):
        text += f"{i}. {format_person(person)}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по ФИО"""
    if not context.args:
        await update.message.reply_text("❌ Укажите фамилию: `/search_name Иванов`", parse_mode="Markdown")
        return
    
    name = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Поиск по имени: {name}...")
    
    # Кодируем кириллицу для URL
    encoded_name = urllib.parse.quote(name)
    data = await api_request("/search/name", {"name": encoded_name, "limit": 5})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    
    total = data.get("total", 0)
    if total == 0:
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    text = f"📝 *Найдено: {total} записей*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, person in enumerate(data.get("results", [])[:5], 1):
        text += f"{i}. {format_person(person)}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def search_inn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по ИНН"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ИНН: `/search_inn 910214822591`", parse_mode="Markdown")
        return
    
    inn = context.args[0]
    await update.message.reply_text(f"🔍 Поиск по ИНН: {inn}...")
    
    data = await api_request("/search/inn", {"inn": inn})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    
    if data.get("status") == "not_found":
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    results = data.get("results", [])
    if not results:
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    person = results[0]
    text = f"🆔 *Найден по ИНН*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += format_person(person)
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def search_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по паспорту"""
    if not context.args:
        await update.message.reply_text("❌ Укажите паспорт: `/search_passport 1234567890`", parse_mode="Markdown")
        return
    
    passport = context.args[0]
    await update.message.reply_text(f"🔍 Поиск по паспорту: {passport}...")
    
    data = await api_request("/search/passport", {"passport": passport})
    
    if data.get("status") == "error":
        await update.message.reply_text(f"❌ Ошибка: {data.get('error')}")
        return
    
    if data.get("status") == "not_found":
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    results = data.get("results", [])
    if not results:
        await update.message.reply_text("❌ Ничего не найдено")
        return
    
    person = results[0]
    text = f"🪪 *Найден по паспорту*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += format_person(person)
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== MAIN ==========
def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("search_phone", search_phone))
    app.add_handler(CommandHandler("search_name", search_name))
    app.add_handler(CommandHandler("search_inn", search_inn))
    app.add_handler(CommandHandler("search_passport", search_passport))
    
    # Запуск
    logger.info(f"🚀 Бот запущен на порту {PORT}")
    
    if os.getenv("RENDER"):
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"https://your-app.onrender.com/webhook"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
