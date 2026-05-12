from django.conf import settings
import telegram
from config import API_TOKEN

# Инициализация бота
bot = telegram.Bot(API_TOKEN)

# --- Вспомогательная функция (твой стиль) ---

def send_user_notification(user_id, message_text):
    """Базовая функция отправки сообщения"""
    bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')

# --- КАТЕГОРИЯ: ПИТАНИЕ ---

def send_morning_food_reminder(user_id):
    text = (
        "📸 *Сегодня нет записей о питании*\n\n"
        "Добавьте фото еды, чтобы корректно рассчитать дневную норму."
    )
    send_user_notification(user_id, text)

def send_calorie_limit_warning(user_id):
    text = (
        "⚠️ *Превышение дневной нормы калорий*\n\n"
        "Сегодня вы превысили рекомендуемую норму."
    )
    send_user_notification(user_id, text)


# --- КАТЕГОРИЯ: ПРИВЫЧКИ ---

def send_habit_confirmation(user_id):
    text = (
        "🔔 *Подтвердите выполнение привычки*\n\n"
        "Отметьте привычку как выполненную."
    )
    send_user_notification(user_id, text)

def send_habit_not_finished_warning(user_id):
    text = (
        "⚠️ *Привычка не выполнена*\n\n"
        "Сегодня привычка не была отмечена."
    )
    send_user_notification(user_id, text)


# --- КАТЕГОРИЯ: ЛЕКАРСТВА ---

def send_medication_reminder(user_id, category, name, course, method):
    text = (
        f"💊 *Напоминание о приёме лекарства:*\n\n"
        f"*Категория:* {category}\n"
        f"*Название:* {name}\n"
        f"*Курс:* {course}\n"
        f"*Способ приёма:* {method}"
    )
    send_user_notification(user_id, text)

def send_missed_medication_warning(user_id, medication_name):
    text = (
        f"⚠️ *Вы пропустили приём лекарства*\n\n"
        f"Сегодня лекарство *{medication_name}* не было отмечено как принято."
    )
    send_user_notification(user_id, text)