import os
from flask import Flask, request
from openai import OpenAI
from dotenv import load_dotenv
import telebot
import json

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML", threaded=False)


# -----------------------------------
# Безопасная отправка сообщения
# -----------------------------------
def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except:
        safe_text = telebot.util.escape_html(text)
        return bot.send_message(chat_id, safe_text)


# -----------------------------------
# GPT ответ
# -----------------------------------
def send_gpt_answer(chat_id, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        answer = response.choices[0].message.content
        safe_send_message(chat_id, answer)
    except Exception as e:
        safe_send_message(chat_id, f"⚠ Ошибка: {e}")


# -----------------------------------
# Webhook endpoint
# -----------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_data().decode("utf-8")
        print("===> Telegram update received:")
        print(data)

        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])
    except Exception as e:
        print("Webhook error:", e)

    return "OK", 200


# -----------------------------------
# Команды Telegram
# -----------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    safe_send_message(message.chat.id, "<b>Привет!</b>\nНапиши мне что-нибудь!")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    safe_send_message(message.chat.id,
                      "<b>Команды:</b>\n/start\n/help\n/gpt <текст>")


@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()
    if not query:
        safe_send_message(message.chat.id, "❗ Напиши текст после /gpt")
        return

    send_gpt_answer(message.chat.id, query)


@bot.message_handler(content_types=
