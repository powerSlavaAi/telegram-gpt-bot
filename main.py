import os
import telebot
from openai import OpenAI
from dotenv import load_dotenv
from telebot.types import BotCommand

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Красивое меню команд ---
bot.set_my_commands(
    [
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Помощь и описание возможностей"),
        BotCommand("profile", "Информация о пользователе"),
        BotCommand("gpt", "Задать вопрос ИИ"),
        BotCommand("info", "Информация о боте"),
    ]
)
# -----------------------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>Привет!</b> Я бот на GPT. Напиши мне что-нибудь!"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message.text}]
        )

        answer = response.choices[0].message.content

        # ❗ Блок оформления убран — отправляем обычный текст
        bot.send_message(message.chat.id, answer)

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "rate_limit" in error_text:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Превышен лимит запросов к OpenAI.</b>\nПодожди 20–30 секунд и попробуй снова."
            )
            return

        bot.send_message(message.chat.id, f"<i>Ошибка:</i> <code>{e}</code>")

bot.polling(none_stop=True)
