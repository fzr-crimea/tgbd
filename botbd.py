from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import os

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

# Главное меню
MAIN_MENU = [["Продукция", "Прайс лист"]]

# Меню продукции
PRODUCT_MENU = [["Рыба", "Мясо"], ["Назад"]]

# Меню прайс-листа
PRICE_MENU = [["Старый прайс-лист", "Акционные цены", "Актуальный прайс"], ["Назад"]]

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
    elif text == "Старый прайс-лист":
        # Отправляем файл old.txt
        with open("old.txt", "rb") as file:
            await update.message.reply_document(
                document=file,
                caption="Старый прайс-лист",
                reply_markup=ReplyKeyboardMarkup([["Назад"]], one_time_keyboard=True, resize_keyboard=True)
            )
    elif text in ["Акционные цены", "Актуальный прайс"]:
        prices = get_prices(text)
        await update.message.reply_text(
            f"Прайс-лист ({text}):\n" + "\n".join(prices),
            reply_markup=ReplyKeyboardMarkup(PRICE_MENU, one_time_keyboard=True, resize_keyboard=True)
        )
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