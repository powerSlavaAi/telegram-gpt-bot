import os
import telebot
from telebot import types
from openai import OpenAI
from dotenv import load_dotenv
from telebot.types import BotCommand

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Меню команд ---
bot.set_my_commands(
    [
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Помощь"),
        BotCommand("gpt", "Задать вопрос ИИ"),
    ]
)

# ---------- Команда /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>Привет!</b>\nЯ бот на GPT. Просто напиши мне любое сообщение.",
    )

# ---------- Обработка текстовых сообщений ----------
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message.text}]
        )

        answer = response.choices[0].message.content

        bot.send_message(
            message.chat.id,
            answer
        )

    except Exception as e:
        error_text = str(e)

        if "429" in error_text:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Превышен лимит запросов.</b> Подожди немного."
            )
            return

        bot.send_message(message.chat.id, f"<i>Ошибка:</i> <code>{e}</code>")

# ---------- Запуск бота ----------
bot.polling(none_stop=True)
