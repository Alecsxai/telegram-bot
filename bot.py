from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

TOKEN = "8799100467:AAGTI4LuX5KQtZ8-TJ55MDKlfyUQpH2mCCs"
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

# ===== Сохранение =====
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
            print("Ошибка загрузки")

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
        return ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([[b] for b in brands] + [["Назад"]], resize_keyboard=True)

def items_menu(category, brand):
    items = data.get(category, {}).get(brand, {})
    if not items:
        return ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([[i] for i in items.keys()] + [["Назад"]], resize_keyboard=True)

# ===== Старт =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["cart"] = []
    await update.message.reply_text("Главное меню", reply_markup=main_menu(update.effective_user.id))

# ===== Основная логика =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # ===== Фото =====
    if update.message.photo:
        if context.user_data.get("state") == "add_photo":
            photo = update.message.photo[-1].file_id
            category = context.user_data["category"]
            brand = context.user_data["brand"]
            name = context.user_data["name"]

            data.setdefault(category, {})
            data[category].setdefault(brand, {})

            data[category][brand][name] = {
                "text": context.user_data["text"],
                "photo": photo
            }

            save_data()
            context.user_data.clear()
            await update.message.reply_text("Добавлено ✅", reply_markup=admin_menu())
        return

    if not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

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

    # ===== ДОБАВЛЕНИЕ =====
    if text == "Добавить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "choose_type"
        await update.message.reply_text("Выбери категорию:", reply_markup=catalog_menu())
        return

    if context.user_data.get("state") == "choose_type":
        if text not in CATEGORIES:
            return
        context.user_data["category"] = CATEGORIES[text]
        context.user_data["state"] = "add_brand"
        await update.message.reply_text("Введите бренд:")
        return

    if context.user_data.get("state") == "add_brand":
        category = context.user_data["category"]
        brand = text

        context.user_data["brand"] = brand
        data.setdefault(category, {})
        data[category].setdefault(brand, {})

        context.user_data["state"] = "add_name"
        await update.message.reply_text("Название товара:")
        return

    if context.user_data.get("state") == "add_name":
        context.user_data["name"] = text
        context.user_data["state"] = "add_text"
        await update.message.reply_text("Описание:")
        return

    if context.user_data.get("state") == "add_text":
        context.user_data["text"] = text
        context.user_data["state"] = "add_photo"
        await update.message.reply_text("Отправьте фото:")
        return

    # ===== УДАЛЕНИЕ =====
    if text == "Удалить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "delete_type"
        await update.message.reply_text("Категория:", reply_markup=catalog_menu())
        return

    if context.user_data.get("state") == "delete_type":
        if text not in CATEGORIES:
            return
        context.user_data["category"] = CATEGORIES[text]
        context.user_data["state"] = "delete_brand"

        if not data.get(CATEGORIES[text]):
            await update.message.reply_text("Нет брендов 🤷‍♂️", reply_markup=admin_menu())
            context.user_data.clear()
            return

        await update.message.reply_text("Бренд:", reply_markup=brands_menu(CATEGORIES[text]))
        return

    if context.user_data.get("state") == "delete_brand":
        context.user_data["brand"] = text
        context.user_data["state"] = "delete_item"

        if not data.get(context.user_data["category"], {}).get(text):
            await update.message.reply_text("Нет товаров 🤷‍♂️", reply_markup=admin_menu())
            context.user_data.clear()
            return

        await update.message.reply_text(
            "Товар:",
            reply_markup=items_menu(context.user_data["category"], text)
        )
        return

    if context.user_data.get("state") == "delete_item":
        category = context.user_data.get("category")
        brand = context.user_data.get("brand")

        if text in data.get(category, {}).get(brand, {}):
            del data[category][brand][text]

            if not data[category][brand]:
                del data[category][brand]

            save_data()
            await update.message.reply_text("Удалено ✅", reply_markup=admin_menu())
        else:
            await update.message.reply_text("Товар не найден ❌", reply_markup=admin_menu())

        context.user_data.clear()
        return

    # ===== КАТАЛОГ =====
    if text == "Каталог":
        await update.message.reply_text("Выберите:", reply_markup=catalog_menu())
        return

    if text in CATEGORIES:
        category = CATEGORIES[text]
        context.user_data["category"] = category

        if not data.get(category):
            await update.message.reply_text("Нет брендов 🤷‍♂️")
            return

        await update.message.reply_text("Бренд:", reply_markup=brands_menu(category))
        return

    if "category" in context.user_data and "brand" not in context.user_data:
        if text not in data.get(context.user_data["category"], {}):
            return

        context.user_data["brand"] = text

        await update.message.reply_text(
            "Товар:",
            reply_markup=items_menu(context.user_data["category"], text)
        )
        return

    # ===== ПРОСМОТР =====
    category = context.user_data.get("category")
    brand = context.user_data.get("brand")

    if text in data.get(category, {}).get(brand, {}):
        item = data[category][brand][text]

        context.user_data["last_item"] = text
        await update.message.reply_photo(photo=item["photo"], caption=item["text"])
        await update.message.reply_text("Добавить в корзину? (да/нет)")
        context.user_data["state"] = "cart_add"
        return

    # ===== ДОБАВИТЬ В КОРЗИНУ =====
    if context.user_data.get("state") == "cart_add":
        if text.lower() == "да":
            item_name = context.user_data.get("last_item")
            if item_name:
                context.user_data.setdefault("cart", []).append(item_name)

            await update.message.reply_text("Добавлено в корзину ✅")
        else:
            await update.message.reply_text("Ок")

        context.user_data["state"] = None
        context.user_data.pop("last_item", None)
        return

    # ===== КОРЗИНА =====
    if text == "Корзина":
        cart = context.user_data.get("cart", [])

        if not cart:
            await update.message.reply_text("Корзина пустая")
            return

        cart_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(cart)])

        await update.message.reply_text(
            f"🛒 В корзине:\n\n{cart_text}\n\n"
            "Введи номер товара для удаления или 'Оформить заказ'"
        )

        context.user_data["state"] = "cart_manage"
        return

    # ===== УПРАВЛЕНИЕ КОРЗИНОЙ =====
    if context.user_data.get("state") == "cart_manage":
        cart = context.user_data.get("cart", [])

        if text.lower() == "оформить заказ":
            user = update.effective_user
            username = f"@{user.username}" if user.username else "без username"

            order_text = f"🛒 Заказ\n{username}\n\n" + "\n".join(cart)

            for admin_id in ADMIN_IDS:
                await context.bot.send_message(admin_id, order_text)

            context.user_data["cart"] = []
            context.user_data["state"] = None

            await update.message.reply_text("Заказ отправлен ✅", reply_markup=main_menu(user_id))
            return

        if text.isdigit():
            index = int(text) - 1
            if 0 <= index < len(cart):
                removed = cart.pop(index)
                await update.message.reply_text(f"Удалено: {removed}")
            else:
                await update.message.reply_text("Неверный номер")

        # обновление списка
        if cart:
            cart_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(cart)])
            await update.message.reply_text(cart_text)
        else:
            await update.message.reply_text("Корзина пустая")

        return

    await update.message.reply_text("Не понял 🤔", reply_markup=main_menu(user_id))


# ===== Запуск =====
load_data()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, handle_message))

print("Бот запущен...")
app.run_polling()