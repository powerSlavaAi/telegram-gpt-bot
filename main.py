import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

# Aiogram 3 объекты
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я GPT-бот. Напиши мне сообщение.")


@router.message()
async def handle_message(message: Message):
    # Ответ от LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": message.text}
        ]
    )

    answer = response.choices[0].message["content"]
    await message.answer(answer)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
