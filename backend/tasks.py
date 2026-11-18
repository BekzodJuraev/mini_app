from django.conf import settings
import telegram
from config import API_TOKEN
from .models import Check_Drugs, Notification_drugs
from datetime import date
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

def send_medication_reminder(user_id, category, name, day,time_day, method,**kwargs):
    text = (
        f"💊 *Напоминание о приёме лекарства:*\n\n"
        f"*Категория:* {category}\n"
        f"*Название:* {name}\n"
        f"*Курс:* {day} дней,{time_day} раза в день\n"
        f"*Способ приёма:* {method}"
    )
    send_user_notification(user_id, text)

def send_missed_medication_warning(user_id, notif_id, **kwargs):
    check = Check_Drugs.objects.filter(
        notification_id=notif_id,
        date=date.today()
    ).first()

    if check is None:
        text = (
            f"⚠️ *Вы пропустили приём лекарства*\n\n"
            f"Сегодня лекарство  не было отмечено как принято."
        )
        send_user_notification(user_id, text)
def send_health_reminder(user_id):
    """Напоминание об измерении давления по макету"""
    text = (
        "🩺 *Пора измерить давление*\n"
        "Сделайте замер давления и\n"
        "внести данные в приложение.\n\n"

    )
    send_user_notification(user_id, text)

def send_female_health_reminder(user_id, title, description, **kwargs):
    """Напоминание по женскому календарю (по макету)"""
    text = (
        f"🔔 *{title}*\n\n"
        f"💊 {description}"
    )
    send_user_notification(user_id, text)

import io
def send_pdf_to_telegram_async(profile, pdf_bytes: bytes, filename: str, caption: str = "Ваш PDF-отчёт"):
    """
    Синхронно отправляет сгенерированный PDF-файл в Telegram-бот по telegram_id
    (если скачивают из детского профиля без своего telegram_id — берет telegram_id родителя).
    """

    tg_id = getattr(profile, 'telegram_id', None)
    if not tg_id and getattr(profile, 'family', None):
        tg_id = getattr(profile.family, 'telegram_id', None)

    if not tg_id:
        return

    try:
        doc_file = io.BytesIO(pdf_bytes)
        doc_file.name = filename
        bot.send_document(
            chat_id=tg_id,
            document=doc_file,
            filename=filename,
            caption=caption
        )
    except Exception as e:
        print(f"Telegram PDF send error: {e}")