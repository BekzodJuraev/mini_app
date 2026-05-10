import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_TOKEN,WEB_APP_URL
# Настрой логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
API_TOKEN = API_TOKEN
WEB_APP_URL = WEB_APP_URL


# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    """
    # Создаем кнопку Web App
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть Web App",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ])

    # Отправляем сообщение с текстом, который ты просил
    await message.answer(
        "Добро пожаловать! Нажмите на кнопку ниже для открытия Web App.",
        reply_markup=markup
    )

async def main():

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")