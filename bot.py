from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import json
import os

TOKEN = "8799100467:AAEypu9YL54Ms-s05NBRCIMXu_55PzOE2cM"
ADMIN_IDS = [1710474238]

DATA_FILE = "data.json"
liquids = {}
systems = {}

# ====== СОХРАНЕНИЕ ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"liquids": liquids, "systems": systems}, f, ensure_ascii=False, indent=4)

def load_data():
    global liquids, systems
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                liquids = data.get("liquids", {})
                systems = data.get("systems", {})
        except:
            liquids = {}
            systems = {}

# ====== ОЧИСТКА ПУСТЫХ БРЕНДОВ ======
def clean_empty_brands():
    empty = [b for b in liquids if not liquids[b]]
    for b in empty:
        print(f"Удаляем пустой бренд: {b}")
        del liquids[b]

# ====== КНОПКИ ======
def main_menu(user_id):
    buttons = [["Каталог"]]
    if user_id in ADMIN_IDS:
        buttons.append(["Админ"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def catalog_menu():
    return ReplyKeyboardMarkup([["В наличии", "Заказать"], ["Назад"]], resize_keyboard=True)

def stock_menu():
    return ReplyKeyboardMarkup([["Жижа", "Подсистемы"], ["Назад"]], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([["Добавить товар", "Удалить товар"], ["Назад"]], resize_keyboard=True)

def type_menu():
    return ReplyKeyboardMarkup([["Жижа", "Подсистемы"]], resize_keyboard=True)

def brands_menu():
    clean_empty_brands()
    buttons = [[name] for name in liquids.keys()]
    buttons.append(["Назад"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def flavors_menu(brand):
    buttons = [[name] for name in liquids.get(brand, {}).keys()]
    buttons.append(["Назад"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def systems_menu():
    buttons = [[name] for name in systems.keys()]
    buttons.append(["Назад"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ====== СТАРТ ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Главное меню", reply_markup=main_menu(update.effective_user.id))

# ====== ТЕКСТ ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()

    user_id = update.effective_user.id
    state = context.user_data.get("state")

    print(f"DEBUG → STATE: {state} | TEXT: {text}")
    print("DEBUG → LIQUIDS:", liquids)

    # ===== НАЗАД =====
    if text == "Назад":
        context.user_data.clear()
        await update.message.reply_text("Главное меню", reply_markup=main_menu(user_id))
        return

    # =========================
    # 🔥 STATE ПРИОРИТЕТ
    # =========================

    if state == "choose_type":
        context.user_data["type"] = text
        if text == "Жижа":
            context.user_data["state"] = "add_brand"
            await update.message.reply_text("Введи бренд:")
        elif text == "Подсистемы":
            context.user_data["state"] = "add_name"
            await update.message.reply_text("Название устройства:")
        return

    if state == "add_brand":
        context.user_data["brand"] = text_lower
        if text_lower not in liquids:
            liquids[text_lower] = {}
        context.user_data["state"] = "add_name"
        await update.message.reply_text("Название товара:")
        return

    if state == "add_name":
        context.user_data["name"] = text
        context.user_data["state"] = "add_text"
        await update.message.reply_text("Описание товара:")
        return

    if state == "add_text":
        context.user_data["text"] = text
        context.user_data["state"] = "add_photo"
        await update.message.reply_text("Отправь фото товара:")
        return

    # ===== УДАЛЕНИЕ =====
    if state == "delete_type":
        context.user_data["type"] = text
        if text == "Жижа":
            context.user_data["state"] = "delete_brand"
            await update.message.reply_text("Выбери бренд:", reply_markup=brands_menu())
        elif text == "Подсистемы":
            context.user_data["state"] = "delete_system"
            await update.message.reply_text("Выбери устройство:", reply_markup=systems_menu())
        return

    if state == "delete_brand":
        for brand in liquids:
            if text_lower == brand.lower():
                context.user_data["brand"] = brand
                context.user_data["state"] = "delete_item"
                await update.message.reply_text("Выбери товар:", reply_markup=flavors_menu(brand))
                return

    if state == "delete_item":
        brand = context.user_data["brand"]

        for item_name in list(liquids.get(brand, {})):
            if text_lower == item_name.lower():
                del liquids[brand][item_name]
                print(f"Удалили товар: {item_name} из {brand}")

                # 🔥 удаляем пустой бренд
                if not liquids[brand]:
                    del liquids[brand]
                    print(f"Удалили пустой бренд: {brand}")

                save_data()
                break

        context.user_data.clear()
        await update.message.reply_text("❌ Удалено", reply_markup=admin_menu())
        return

    if state == "delete_system":
        for name in list(systems):
            if text_lower == name.lower():
                del systems[name]
                save_data()
                break

        context.user_data.clear()
        await update.message.reply_text("❌ Удалено", reply_markup=admin_menu())
        return

    # =========================
    # ⬇️ БЕЗ STATE
    # =========================

    if not state and text == "Каталог":
        await update.message.reply_text("Выбери:", reply_markup=catalog_menu())
        return

    if not state and text == "В наличии":
        await update.message.reply_text("Что выбрать?", reply_markup=stock_menu())
        return

    if not state and text == "Заказать":
        await update.message.reply_text("Напиши администратору @RelaxMist2 📩", reply_markup=catalog_menu())
        return

    if not state and text == "Жижа":
        await update.message.reply_text("Выбери бренд:", reply_markup=brands_menu())
        return

    if not state and text == "Подсистемы":
        await update.message.reply_text("Выбери устройство:", reply_markup=systems_menu())
        return

    if text == "Админ":
        if user_id in ADMIN_IDS:
            await update.message.reply_text("Админ-панель", reply_markup=admin_menu())
        else:
            await update.message.reply_text("Нет доступа ❌")
        return

    if text == "Добавить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "choose_type"
        await update.message.reply_text("Что добавить?", reply_markup=type_menu())
        return

    if text == "Удалить товар" and user_id in ADMIN_IDS:
        context.user_data["state"] = "delete_type"
        await update.message.reply_text("Что удалить?", reply_markup=type_menu())
        return

    # ===== ПРОСМОТР ЖИЖИ =====
    if not state:
        for brand in liquids:
            if text_lower == brand.lower():
                context.user_data["brand"] = brand
                await update.message.reply_text(f"{brand}:", reply_markup=flavors_menu(brand))
                return

    if not state and "brand" in context.user_data:
        brand = context.user_data["brand"]
        for item_name in liquids.get(brand, {}):
            if text_lower == item_name.lower():
                item = liquids[brand][item_name]
                await update.message.reply_photo(photo=item["photo"], caption=item["text"])
                return

    # ===== ПРОСМОТР ПОДСИСТЕМ =====
    if not state:
        for name in systems:
            if text_lower == name.lower():
                item = systems[name]
                await update.message.reply_photo(photo=item["photo"], caption=item["text"])
                return

    await update.message.reply_text("Не понял 🤔", reply_markup=main_menu(user_id))

# ====== ФОТО ======
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    print(f"DEBUG PHOTO → STATE: {state}")

    if state == "add_photo":
        photo = update.message.photo[-1].file_id
        name = context.user_data["name"]
        item_type = context.user_data.get("type")

        if item_type == "Жижа":
            brand = context.user_data["brand"]
            liquids[brand][name] = {
                "text": context.user_data["text"],
                "photo": photo
            }

        elif item_type == "Подсистемы":
            systems[name] = {
                "text": context.user_data["text"],
                "photo": photo
            }

        save_data()
        context.user_data.clear()

        await update.message.reply_text("✅ Добавлено!", reply_markup=admin_menu())
    else:
        await update.message.reply_text("Фото сейчас не нужно 🤔")

# ====== ЗАПУСК ======
load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Бот запущен...")
app.run_polling(drop_pending_updates=True)