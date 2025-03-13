from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import os

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

# Главное меню
MAIN_MENU = [["Продукция", "Прайс лист"], ["Редактировать данные"]]

# Меню продукции
PRODUCT_MENU = [["Рыба", "Мясо"], ["Назад"]]

# Меню прайс-листа
PRICE_MENU = [["Старый прайс-лист", "Акционные цены", "Актуальный прайс"], ["Назад"]]

# Меню редактирования
EDIT_MENU = [["Изменить продукт", "Изменить прайс-лист"], ["Назад"]]

# Создаем базу данных и таблицы, если они не существуют
def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Таблица для продукции
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    # Таблица для прайс-листов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_type TEXT NOT NULL
        )
    """)

    # Добавляем тестовые данные, если таблицы пусты
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [
            ("Лосось", "Рыба"),
            ("Форель", "Рыба"),
            ("Говядина", "Мясо"),
            ("Свинина", "Мясо")
        ]
        cursor.executemany("INSERT INTO products (name, category) VALUES (?, ?)", products)

    cursor.execute("SELECT COUNT(*) FROM prices")
    if cursor.fetchone()[0] == 0:
        prices = [
            ("Прайс-лист 2022", "Старый прайс-лист"),
            ("Акции на рыбу", "Акционные цены"),
            ("Прайс-лист 2023", "Актуальный прайс")
        ]
        cursor.executemany("INSERT INTO prices (name, price_type) VALUES (?, ?)", prices)

    conn.commit()
    conn.close()

# Функция для получения данных из таблицы products
def get_products(category: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE category = ?", (category,))
    products = cursor.fetchall()
    conn.close()
    return [product[0] for product in products]

# Функция для получения данных из таблицы prices
def get_prices(price_type: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM prices WHERE price_type = ?", (price_type,))
    prices = cursor.fetchall()
    conn.close()
    return [price[0] for price in prices]

# Функция для обновления названия продукта
def update_product_name(old_name: str, new_name: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ? WHERE name = ?", (new_name, old_name))
    conn.commit()
    conn.close()

# Функция для обновления категории продукта
def update_product_category(name: str, new_category: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET category = ? WHERE name = ?", (new_category, name))
    conn.commit()
    conn.close()

# Функция для обновления названия прайс-листа
def update_price_name(old_name: str, new_name: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE prices SET name = ? WHERE name = ?", (new_name, old_name))
    conn.commit()
    conn.close()

# Функция для обновления типа прайс-листа
def update_price_type(name: str, new_type: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE prices SET price_type = ? WHERE name = ?", (new_type, name))
    conn.commit()
    conn.close()

# Функция для отправки главного меню
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Выберите раздел:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
    )

# Обработка нажатий на кнопки
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if text == "Продукция":
        await update.message.reply_text(
            "Выберите категорию:",
            reply_markup=ReplyKeyboardMarkup(PRODUCT_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text == "Прайс лист":
        await update.message.reply_text(
            "Выберите тип прайс-листа:",
            reply_markup=ReplyKeyboardMarkup(PRICE_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text == "Редактировать данные":
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(EDIT_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text == "Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text in ["Рыба", "Мясо"]:
        products = get_products(text)
        await update.message.reply_text(
            f"Продукция ({text}):\n" + "\n".join(products),
            reply_markup=ReplyKeyboardMarkup(PRODUCT_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text in ["Старый прайс-лист", "Акционные цены", "Актуальный прайс"]:
        prices = get_prices(text)
        await update.message.reply_text(
            f"Прайс-лист ({text}):\n" + "\n".join(prices),
            reply_markup=ReplyKeyboardMarkup(PRICE_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
    elif text == "Изменить продукт":
        await update.message.reply_text(
            "Введите старое название продукта и новое название через запятую (например, Лосось, Сёмга):"
        )
        context.user_data["action"] = "update_product_name"
    elif text == "Изменить прайс-лист":
        await update.message.reply_text(
            "Введите старое название прайс-листа и новое название через запятую (например, Прайс-лист 2022, Прайс-лист 2021):"
        )
        context.user_data["action"] = "update_price_name"
    else:
        if "action" in context.user_data:
            if context.user_data["action"] == "update_product_name":
                try:
                    old_name, new_name = text.split(", ")
                    update_product_name(old_name, new_name)
                    await update.message.reply_text(f"Название продукта изменено: {old_name} -> {new_name}")
                except Exception as e:
                    await update.message.reply_text(f"Ошибка: {e}")
            elif context.user_data["action"] == "update_price_name":
                try:
                    old_name, new_name = text.split(", ")
                    update_price_name(old_name, new_name)
                    await update.message.reply_text(f"Название прайс-листа изменено: {old_name} -> {new_name}")
                except Exception as e:
                    await update.message.reply_text(f"Ошибка: {e}")
            context.user_data.clear()
        else:
            await update.message.reply_text(
                "Пожалуйста, используйте кнопки для навигации.",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
            )

# Запуск бота
def main() -> None:
    # Создаем базу данных и таблицы, если они не существуют
    create_database()

    # Укажите ваш токен
    application = Application.builder().token("8193222159:AAGQZOam4mhgwGdyQF_xcdaflqO6XY9rrn0").build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()