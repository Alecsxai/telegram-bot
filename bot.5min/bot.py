from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import aiohttp  # для http-запросов
import os
import json

TOKEN = "ВАШ_ТОКЕН_БОТА"
ADMIN_IDS = [123456789]  # Ваш Telegram ID
DATA_FILE = "data.json"

# ====== ДАННЫЕ ======
liquids = {}
systems = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"liquids": liquids, "systems": systems}, f, ensure_ascii=False, indent=4)

def load_data():
    global liquids, systems
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            liquids = data.get("liquids", {})
            systems = data.get("systems", {})

# ====== КНОПКИ ======
def main_menu(user_id):
    buttons = [["Каталог"]]
    if user_id in ADMIN_IDS:
        buttons.append(["Админ"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ====== СТАРТ ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен ✅", reply_markup=main_menu(update.effective_user.id))

# ====== ФОНОВАЯ ЗАДАЧА ======
async def periodic_task(app):
    """
    Эта функция будет выполняться каждые 5 минут
    """
    while True:
        try:
            # Пример запроса к API
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coindesk.com/v1/bpi/currentprice.json") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print("Обновлено:", data["bpi"]["USD"]["rate"])
                    else:
                        print("Ошибка запроса:", resp.status)
        except Exception as e:
            print("Ошибка в периодическом задании:", e)

        await asyncio.sleep(300)  # 5 минут = 300 секунд

# ====== ЗАПУСК ======
async def main():
    load_data()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Запускаем периодическую задачу в фоне
    app.job_queue.run_repeating(lambda ctx: asyncio.create_task(periodic_task(app)), interval=300, first=0)

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())