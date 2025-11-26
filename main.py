import os
from flask import Flask, request
from openai import OpenAI
from dotenv import load_dotenv
import telebot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


# ===============================
#   Безопасная отправка HTML
# ===============================
def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception:
        safe_text = telebot.util.escape_html(text)
        return bot.send_message(chat_id, safe_text)


# ===============================
#   GPT ответ
# ===============================
def send_gpt_answer(chat_id, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        answer = response.choices[0].message.content
        safe_send_message(chat_id, answer)
    except Exception as e:
        safe_send_message(chat_id, f"⚠️ Ошибка: {e}")


# ===============================
#   Telegram Webhook endpoint
# ===============================
@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = request.get_data().decode("utf-8")
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200


# ===============================
#   Команда /start
# ===============================
@bot.message_handler(commands=['start'])
def start(message):
    safe_send_message(
        message.chat.id,
        "<b>Привет!</b>\nЯ бот на GPT. Просто напиши мне любое сообщение."
    )


# ===============================
#   Команда /help
# ===============================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    safe_send_message(
        message.chat.id,
        "<b>Доступные команды:</b>\n"
        "/start – запуск бота\n"
        "/help – помощь\n"
        "/gpt <текст> – задать вопрос ChatGPT"
    )


# ===============================
#   Команда /gpt
# ===============================
@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()

    if not query:
        safe_send_message(message.chat.id, "❗ Напиши текст после команды /gpt")
        return

    send_gpt_answer(message.chat.id, query)


# ===============================
#   Обычный текст → GPT
# ===============================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)


# ===============================
#   Главная страница для проверки
# ===============================
@app.route("/")
def home():
    return "Bot is running!", 200


# ===============================
#   Запуск Flask (Render сам вызывает)
# ===============================
