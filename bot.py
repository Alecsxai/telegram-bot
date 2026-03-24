from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import json
import os

TOKEN = "8799100467:AAEypu9YL54Ms-s05NBRCIMXu_55PzOE2cM"
ADMIN_IDS = [1710474238]

DATA_FILE = "data.json"

# ===== ДАННЫЕ =====
data = {
    "liquids": {},
    "systems": {},
    "consumables": {}
}

# ===== КОРЗИНА =====
carts = {}

# ===== СОХРАНЕНИЕ =====
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

# ===== КНОПКИ =====
def main_menu(user_id):
    buttons = [["Каталог", "Корзина"]]
    if user_id in ADMIN_IDS:
        buttons.append(["Админ"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def catalog_menu():
    return ReplyKeyboardMarkup([["В наличии"], ["Назад"]], resize_keyboard=True)

def stock_menu():
    return ReplyKeyboardMarkup(
        [["Жижа", "Подсистемы", "Расходники"], ["Назад"]],
        resize_keyboard=True
    )

def admin_menu():
    return ReplyKeyboardMarkup(
        [["Добавить", "Удалить"], ["Назад"]],
        resize_keyboard=True
    )

def type_menu():
    return ReplyKeyboardMarkup(
        [["Жижа", "Подсистемы", "Расходники"]],
        resize_keyboard=True
    )

def brands_menu(category):
    buttons = [[b] for b in data[category]]
    buttons.append(["Назад"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def items_menu(category, brand):
    buttons = [[i] for i in data[category].get(brand, {})]
    buttons.append(["Назад"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Главное меню", reply_markup=main_menu(update.effective_user.id))

# ===== КОРЗИНА =====
def get_cart(user_id):
    if user_id not in carts:
        carts[user_id] = []
    return carts[user_id]

# ===== ЛОГИКА =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get("state")

    # ===== НАЗАД =====
    if text == "Назад":
        context.user_data.clear()
        await update.message.reply_text("Главное меню", reply_markup=main_menu(user_id))
        return

    # ===== КОРЗИНА =====
    if text == "Корзина":
        cart = get_cart(user_id)
        if not cart:
            await update.message.reply_text("Корзина пуста")
        else:
            msg = "\n".join(cart)
            await update.message.reply_text(f"🛒 В корзине:\n{msg}\n\nНапиши 'Очистить'")
        return

    if text == "Очистить":
        carts[user_id] = []
        await update.message.reply_text("Корзина очищена")
        return

    # ===== STATE =====
    if state == "add_type":
        context.user_data["category"] = text.lower_map = {
            "Жижа": "liquids",
            "Подсистемы": "systems",
            "Расходники": "consumables"
        }[text]
        context.user_data["state"] = "add_brand"
        await update.message.reply_text("Введи бренд:")
        return

    if state == "add_brand":
        context.user_data["brand"] = text
        if text not in data[context.user_data["category"]]:
            data[context.user_data["category"]][text] = {}
        context.user_data["state"] = "add_name"
        await update.message.reply_text("Название товара:")
        return

    if state == "add_name":
        context.user_data["name"] = text
        context.user_data["state"] = "add_text"
        await update.message.reply_text("Описание:")
        return

    if state == "add_text":
        context.user_data["text"] = text
        context.user_data["state"] = "add_photo"
        await update.message.reply_text("Отправь фото")
        return

    # ===== АДМИН =====
    if text == "Админ" and user_id in ADMIN_IDS:
        await update.message.reply_text("Админка", reply_markup=admin_menu())
        return

    if text == "Добавить" and user_id in ADMIN_IDS:
        context.user_data["state"] = "add_type"
        await update.message.reply_text("Выбери тип", reply_markup=type_menu())
        return

    # ===== КАТАЛОГ =====
    if text == "Каталог":
        await update.message.reply_text("Выбери:", reply_markup=catalog_menu())
        return

    if text == "В наличии":
        await update.message.reply_text("Категории:", reply_markup=stock_menu())
        return

    # ===== ВЫБОР КАТЕГОРИИ =====
    mapping = {
        "Жижа": "liquids",
        "Подсистемы": "systems",
        "Расходники": "consumables"
    }

    if text in mapping:
        context.user_data["category"] = mapping[text]
        await update.message.reply_text("Выбери бренд:", reply_markup=brands_menu(mapping[text]))
        return

    # ===== ВЫБОР БРЕНДА =====
    if "category" in context.user_data:
        cat = context.user_data["category"]
        if text in data[cat]:
            context.user_data["brand"] = text
            await update.message.reply_text("Выбери товар:", reply_markup=items_menu(cat, text))
            return

    # ===== ВЫБОР ТОВАРА =====
    if "brand" in context.user_data:
        cat = context.user_data["category"]
        brand = context.user_data["brand"]

        if text in data[cat].get(brand, {}):
            item = data[cat][brand][text]
            context.user_data["last_item"] = text
            await update.message.reply_photo(
                photo=item["photo"],
                caption=item["text"] + "\n\nНапиши 'В корзину'"
            )
            return

    # ===== ДОБАВИТЬ В КОРЗИНУ =====
    if text == "В корзину" and "last_item" in context.user_data:
        cart = get_cart(user_id)
        cart.append(context.user_data["last_item"])
        await update.message.reply_text("Добавлено в корзину 🛒")
        return

    await update.message.reply_text("Не понял 🤔")

# ===== ФОТО =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") == "add_photo":
        photo = update.message.photo[-1].file_id
        cat = context.user_data["category"]
        brand = context.user_data["brand"]
        name = context.user_data["name"]

        data[cat][brand][name] = {
            "text": context.user_data["text"],
            "photo": photo
        }

        save_data()
        context.user_data.clear()

        await update.message.reply_text("Добавлено ✅")

# ===== ЗАПУСК =====
load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Бот запущен...")
app.run_polling()