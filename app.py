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


def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception:
        safe_text = telebot.util.escape_html(text)
        return bot.send_message(chat_id, safe_text)


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


@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200


@bot.message_handler(commands=["start"])
def start(message):
    safe_send_message(
        message.chat.id,
        "<b>Привет!</b>\nЯ бот на GPT. Напиши сообщение."
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    safe_send_message(
        message.chat.id,
        "<b>Команды:</b>\n"
        "/start – запуск\n"
        "/help – помощь\n"
        "/gpt текст – вопрос GPT"
    )


@bot.message_handler(commands=["gpt"])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()
    if not query:
        safe_send_message(message.chat.id, "❗ Напиши текст после /gpt")
        return
    send_gpt_answer(message.chat.id, query)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)


@app.route("/")
def home():
    return "Bot is running!", 200


WEBHOOK_URL = "https://telegram-gpt-bot-m6d8.onrender.com/webhook"

bot.remove_webhook()
bot.set_webhook(WEBHOOK_URL)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
