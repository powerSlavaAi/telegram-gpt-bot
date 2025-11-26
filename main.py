import os
import telebot
from telebot import types
from openai import OpenAI
from dotenv import load_dotenv
from telebot.types import BotCommand
from flask import Flask, request

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_BASE = os.getenv("WEBHOOK_BASE")  # https://your-app.onrender.com

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# --- безопасная отправка ---
def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        err = str(e)
        if ("can't parse entities" in err
            or "Unsupported start tag" in err
            or "Bad Request: can't parse entities" in err):
            safe_text = telebot.util.escape_html(text)
            return bot.send_message(chat_id, safe_text)
        else:
            raise

# --- команды ---
bot.set_my_commands([
    BotCommand("start", "Запустить бота"),
    BotCommand("help", "Помощь"),
    BotCommand("gpt", "Задать вопрос ИИ"),
])

# --- handlers (оставляем логику как у тебя) ---
@bot.message_handler(commands=['start'])
def start(message):
    safe_send_message(message.chat.id, "<b>Привет!</b>\nЯ бот на GPT.", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    safe_send_message(message.chat.id, "<b>Доступные команды:</b>\n/start /help /gpt", parse_mode="HTML")

@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()
    if not query:
        safe_send_message(message.chat.id, "❗ Напиши текст после команды /gpt")
        return
    send_gpt_answer(message.chat.id, query)

def send_gpt_answer(chat_id, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        answer = response.choices[0].message.content
        safe_send_message(chat_id, answer, parse_mode="HTML")
    except Exception as e:
        error_text = str(e)
        if "429" in error_text or "insufficient_quota" in error_text:
            safe_send_message(chat_id, "⚠️ <b>Лимит OpenAI исчерпан.</b>\nПопробуй позже.", parse_mode="HTML")
            return
        safe_send_message(chat_id, "⚠️ Ошибка. Попробуй снова позже.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)

# --- webhook endpoint ---
@app.route("/webhook", methods=["POST"])
def webhook_handler():
    update_json = request.get_json(force=True)
    update = telebot.types.Update.de_json(update_json)
    bot.process_new_updates([update])
    return "", 200

@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# --- устанавливаем webhook при старте (если задан WEBHOOK_BASE) ---
def set_webhook():
    if not WEBHOOK_BASE:
        print("WEBHOOK_BASE не задан — webhook не будет установлен автоматически.")
        return
    webhook_url = WEBHOOK_BASE.rstrip("/") + "/webhook"
    print("Setting webhook to:", webhook_url)
    bot.remove_webhook()
    ok = bot.set_webhook(webhook_url)
    print("Webhook set:", ok)

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
else:
    # при загрузке в gunicorn/render
    set_webhook()
