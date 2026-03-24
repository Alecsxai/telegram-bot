from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

TOKEN = "8799100467:AAEypu9YL54Ms-s05NBRCIMXu_55PzOE2cM"
ADMIN_IDS = [1710474238]

DATA_FILE = "data.json"

CATEGORIES = {
    "Жижа": "liquids",
    "Подсистемы": "systems",
    "Расходники": "consumables"
}

data = {
    "liquids": {},
    "systems": {},
    "consumables": {}
}

# ===== Сохранение данных =====
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass

# ===== Меню =====
def main_menu(user_id):
    buttons = [["Каталог", "Корзина"]]
    if user_id in ADMIN_IDS:
        buttons.append(["Админ"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def catalog_menu():
    return ReplyKeyboardMarkup([list(CATEGORIES.keys()), ["Назад"]], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([["Добавить товар", "Удалить товар"], ["Назад"]], resize_keyboard=True)

def brands_menu(category):
    brands = list(data.get(category, {}).keys())
    if not brands:
        return ReplyKeyboardMarkup([["Нет брендов"], ["Назад"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([[b] for b in brands] + [["Назад"]], resize_keyboard=True)

def items_menu(category, brand):
    items = data.get(category, {}).get(brand, {})
    if not isinstance(items, dict) or not items:
        return ReplyKeyboardMarkup([["Нет товаров"], ["Назад"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([[i] for i in items.keys()] + [["Назад"]], resize_keyboard=True)

# ===== Старт =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["cart"] = []
    await update.message.reply_text("Главное меню", reply_markup=main_menu(update.effective_user.id))

# ===== Обработка сообщений =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # ===== Фото =====
    if update.message.photo:
        if context.user_data.get("state") == "add_photo":
            photo = update.message.photo[-1].file_id
            category = context.user_data["category"]
            brand = context.user_data["brand"]
            name = context.user_data["name"]

            data[category][brand][name] = {
                "text": context.user_data["text"],
                "photo": photo
            }
            save_data()
            context.user_data.clear()
            await update.message.reply_text("Добавлено ✅", reply_markup=admin_menu())
        return

    # ===== Текст =====
    if not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    state = context.user_data.get("state")

    if text in ["Нет брендов", "Нет товаров"]:
        await update.message.reply_text("Пусто 🤷‍♂️")
        return

    # ===== Назад =====
    if text == "Назад":
        cart = context.user_data.get("cart", [])
        context.user_data.clear()
        context.user_data["cart"] = cart
        await update.message.reply_text("Главное меню", reply_markup=main_menu(user_id))
        return

    # ===== Админ =====
    if text == "Админ":
        if user_id in ADMIN_IDS:
            await update.message.reply_text("Админ-панель", reply_markup=admin_menu())
        else:
            await update.message.reply_text("Нет доступа ❌")
        return

    # ===== Добавление товара =====
    if text == "Добавить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "choose_type"
        await update.message.reply_text("Выбери категорию:", reply_markup=catalog_menu())
        return

    if state == "choose_type":
        if text not in CATEGORIES:
            return
        context.user_data["category"] = CATEGORIES[text]
        context.user_data["state"] = "add_brand"
        await update.message.reply_text("Введите бренд:")
        return

    if state == "add_brand":
        category = context.user_data["category"]
        brand = text
        context.user_data["brand"] = brand
        if brand not in data[category]:
            data[category][brand] = {}
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
        await update.message.reply_text("Отправьте фото:")
        return

    # ===== Удаление товара =====
    if text == "Удалить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "delete_type"
        await update.message.reply_text("Категория:", reply_markup=catalog_menu())
        return

    if state == "delete_type":
        if text not in CATEGORIES:
            return
        context.user_data["category"] = CATEGORIES[text]
        context.user_data["state"] = "delete_brand"
        await update.message.reply_text("Бренд:", reply_markup=brands_menu(CATEGORIES[text]))
        return

    if state == "delete_brand":
        context.user_data["brand"] = text
        context.user_data["state"] = "delete_item"
        await update.message.reply_text("Товар:", reply_markup=items_menu(
            context.user_data["category"], text))
        return

    if state == "delete_item":
        category = context.user_data["category"]
        brand = context.user_data["brand"]

        data[category][brand].pop(text, None)

        if not data[category][brand]:
            del data[category][brand]

        save_data()
        context.user_data.clear()
        await update.message.reply_text("Удалено ✅", reply_markup=admin_menu())
        return

    # ===== Каталог =====
    if text == "Каталог":
        await update.message.reply_text("Выберите:", reply_markup=catalog_menu())
        return

    if text in CATEGORIES:
        category = CATEGORIES[text]
        context.user_data["category"] = category
        await update.message.reply_text("Бренд:", reply_markup=brands_menu(category))
        return

    if "category" in context.user_data and "brand" not in context.user_data:
        context.user_data["brand"] = text
        await update.message.reply_text("Товар:", reply_markup=items_menu(
            context.user_data["category"], text))
        return

    # ===== Просмотр товара =====
    category = context.user_data.get("category")
    brand = context.user_data.get("brand")
    item = data.get(category, {}).get(brand, {}).get(text)

    if item:
        context.user_data["last_item"] = text
        await update.message.reply_photo(photo=item["photo"], caption=item["text"])
        await update.message.reply_text("Добавить в корзину? (да/нет)")
        context.user_data["state"] = "cart_add"
        return

    # ===== Добавление в корзину (исправлено: товар бесконечный) =====
    if state == "cart_add":
        if text.lower() == "да":
            item_name = context.user_data.get("last_item")
            if item_name:
                context.user_data.setdefault("cart", []).append(item_name)
                await update.message.reply_text(
                    f"Добавлено в корзину ✅\nМожно добавить ещё или выбрать другой товар",
                    reply_markup=items_menu(
                        context.user_data.get("category"),
                        context.user_data.get("brand")
                    )
                )
        # убираем блокировку
        context.user_data["state"] = None
        context.user_data.pop("last_item", None)
        return

    # ===== Корзина =====
    if text == "Корзина":
        cart = context.user_data.get("cart", [])
        if not cart:
            await update.message.reply_text("Корзина пустая")
            return
        await update.message.reply_text(
            "В корзине:\n" + "\n".join(cart) + "\n\nВведите 'Оформить заказ' для отправки админу или 'Назад'",
        )
        return

    # ===== Оформление заказа =====
    if text == "Оформить заказ":
        cart = context.user_data.get("cart", [])
        if not cart:
            await update.message.reply_text("Корзина пустая")
            return

        user = update.effective_user
        username = f"@{user.username}" if user.username else "без username"

        order_text = (
            f"🛒 НОВЫЙ ЗАКАЗ\n\n"
            f"👤 {username}\n"
            f"🆔 {user.id}\n\n"
            f"📦:\n" + "\n".join(cart)
        )

        for admin_id in ADMIN_IDS:
            await context.bot.send_message(admin_id, order_text)

        context.user_data["cart"].clear()
        await update.message.reply_text("Заказ отправлен ✅", reply_markup=main_menu(user_id))
        return

    await update.message.reply_text("Не понял 🤔", reply_markup=main_menu(user_id))

# ===== Запуск =====
load_data()
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, handle_message))

print("Бот запущен...")
app.run_polling()