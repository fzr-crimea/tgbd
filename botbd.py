from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import os
from datetime import datetime

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

# Ваш user_id (замените на ваш реальный ID)
ADMIN_USER_ID = 154554550  # Укажите ваш user_id

# Главное меню
MAIN_MENU = [["Продукция", "Прайс лист"], ["Статистика"]]

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

    # Таблица для статистики действий пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица для общей статистики
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_users INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
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

# Функция для записи действия пользователя
def log_user_action(user_id: int, action: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_actions (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()
    conn.close()

# Функция для обновления общей статистики
def update_bot_usage():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Обновляем количество пользователей
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions")
    total_users = cursor.fetchone()[0]

    # Обновляем количество сообщений
    cursor.execute("SELECT COUNT(*) FROM user_actions")
    total_messages = cursor.fetchone()[0]

    # Обновляем запись в таблице bot_usage
    cursor.execute("""
        INSERT INTO bot_usage (total_users, total_messages)
        VALUES (?, ?)
        ON CONFLICT(id) DO UPDATE SET
            total_users = excluded.total_users,
            total_messages = excluded.total_messages,
            last_updated = CURRENT_TIMESTAMP
    """, (total_users, total_messages))

    conn.commit()
    conn.close()

# Функция для получения статистики
def get_bot_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Общее количество пользователей
    cursor.execute("SELECT total_users FROM bot_usage")
    total_users = cursor.fetchone()[0]

    # Общее количество сообщений
    cursor.execute("SELECT total_messages FROM bot_usage")
    total_messages = cursor.fetchone()[0]

    # Самые популярные действия
    cursor.execute("SELECT action, COUNT(*) as count FROM user_actions GROUP BY action ORDER BY count DESC LIMIT 5")
    top_actions = cursor.fetchall()

    conn.close()
    return total_users, total_messages, top_actions

# Функция для отправки главного меню
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    log_user_action(user_id, "start")  # Логируем запуск бота
    update_bot_usage()  # Обновляем общую статистику

    # Отправляем картинку и клавиатуру
    with open("12.png", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="Добро пожаловать!",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
        )

# Обработка нажатий на кнопки
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    # Логируем действие пользователя
    log_user_action(user_id, f"button_pressed:{text}")
    update_bot_usage()  # Обновляем общую статистику

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
    elif text == "Статистика":
        if user_id == ADMIN_USER_ID:  # Проверяем, является ли пользователь администратором
            total_users, total_messages, top_actions = get_bot_stats()
            stats_message = (
                f"📊 Статистика бота:\n"
                f"👤 Всего пользователей: {total_users}\n"
                f"💬 Всего сообщений: {total_messages}\n"
                f"🚀 Топ-5 действий:\n"
            )
            for action, count in top_actions:
                stats_message += f"- {action}: {count} раз\n"
            await update.message.reply_text(
                stats_message,
                reply_markup=ReplyKeyboardMarkup([["Назад"]], one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                "У вас нет доступа к статистике.",
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