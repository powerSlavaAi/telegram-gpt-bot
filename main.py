import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

client = OpenAI(api_key=OPENAI_API_KEY)

@dp.message_handler()
async def handle_message(message: types.Message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": message.text}
        ]
    )
    answer = response.choices[0].message["content"]
    await message.reply(answer)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
