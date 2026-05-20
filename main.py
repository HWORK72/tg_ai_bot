import os
import asyncio
import traceback
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    print("🚨 ОШИБКА: Токены не найдены! Проверь файл .env")
    exit()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Здесь хранится история сообщений: ключ - ID юзера, значение - список сообщений
user_context = {}
MAX_HISTORY = 10  # Храним последние 10 сообщений (5 вопросов + 5 ответов)


# Создаем постоянную клавиатуру с кнопкой очистки
def get_keyboard():
    kb = [
        [KeyboardButton(text="🧹 Очистить память")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


async def ask_openrouter(messages_list: list) -> tuple[str, str]:
    """Принимает готовый список истории сообщений и отправляет в API"""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/my-tg-bot",
        "X-Title": "My Local TG Bot"
    }

    payload = {
        "model": "openrouter/free",
        "messages": messages_list
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenRouter API Error {response.status}: {error_text}")

            data = await response.json()
            answer = data['choices'][0]['message']['content']
            actual_model = data.get('model', 'Неизвестная бесплатная модель')

            return answer, actual_model


@dp.message(CommandStart())
async def cmd_start(message: Message):
    # При старте обнуляем память конкретного юзера
    user_context[message.from_user.id] = []
    await message.answer(
        "Привет! Я умный ИИ-ассистент.\n\n"
        "Я запоминаю контекст нашего диалога, поэтому мы можем общаться как обычные люди. "
        "Когда захочешь начать новую тему, просто нажми кнопку очистки памяти.",
        reply_markup=get_keyboard()
    )


@dp.message(F.text == "🧹 Очистить память")
async def clear_memory(message: Message):
    # Очищаем память
    user_context[message.from_user.id] = []
    await message.answer(
        "✅ <b>Память очищена!</b>\nЯ забыл всё, о чем мы говорили. Начнем с чистого листа.",
        parse_mode="HTML",
        reply_markup=get_keyboard()
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    await message.answer("Извини, пока принимаю только текст. Картинки прикрутим чуть позже!")


@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id

    # Если юзер написал впервые (без /start), создаем ему пустую память
    if user_id not in user_context:
        user_context[user_id] = []

    # 1. Сохраняем вопрос пользователя в его личную историю
    user_context[user_id].append({"role": "user", "content": message.text})

    # 2. Обрезаем историю, если она стала слишком длинной
    if len(user_context[user_id]) > MAX_HISTORY:
        user_context[user_id] = user_context[user_id][-MAX_HISTORY:]

    # 3. Формируем финальный список для API: Системная инструкция + История юзера
    api_messages = [
                       {"role": "system", "content": "Отвечай строго на грамотном и естественном русском языке."}
                   ] + user_context[user_id]

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Передаем весь список сообщений в API
        answer, used_model = await ask_openrouter(api_messages)

        # 4. Сохраняем ответ нейросети в историю, чтобы она помнила свои слова
        user_context[user_id].append({"role": "assistant", "content": answer})

        final_text = f"{answer}\n\n<i>🤖 Ответила модель: {used_model}</i>"
        await message.answer(final_text, parse_mode="HTML", reply_markup=get_keyboard())

    except Exception as e:
        # Если API упало с ошибкой, удаляем последний вопрос из памяти,
        # чтобы история не сломалась и юзер мог задать его заново
        if user_context[user_id]:
            user_context[user_id].pop()

        print(f"🚨 ОШИБКА В ТЕРМИНАЛЕ:\n{str(e)}\n{traceback.format_exc()}")
        await message.answer(
            "<b>Упс, техническая заминка!</b> 🛠\n\nСерверы временно недоступны. Пожалуйста, подождите пару минут и отправьте сообщение снова.",
            parse_mode="HTML"
        )


async def main():
    try:
        print("🚀 Бот запущен локально! Индивидуальная память для юзеров включена.")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Polling error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")