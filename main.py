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


# ===============================  
#   БЕЗОПАСНАЯ ОТПРАВКА СООБЩЕНИЙ  
# ===============================
def safe_send_message(chat_id, text, **kwargs):
    """
    Пытается отправить text с parse_mode.
    Если Telegram ругается на HTML — отправляет текст без форматирования.
    """
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        err = str(e)

        # Ошибки HTML-разметки
        if ("can't parse entities" in err
            or "Unsupported start tag" in err
            or "Bad Request: can't parse entities" in err):

            safe_text = telebot.util.escape_html(text)
            return bot.send_message(chat_id, safe_text)

        else:
            raise


# ==========================
#   Меню команд Telegram
# ==========================
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
    safe_send_message(
        message.chat.id,
        "<b>Привет!</b>\nЯ бот на GPT. Просто напиши мне любое сообщение.",
        parse_mode="HTML"
    )


# ---------- Команда /help ----------
@bot.message_handler(commands=['help'])
def help_cmd(message):
    safe_send_message(
        message.chat.id,
        "<b>Доступные команды:</b>\n"
        "/start – запуск бота\n"
        "/help – помощь\n"
        "/gpt <текст> – задать вопрос ChatGPT\n"
        "\nПросто напиши любое сообщение, и я отвечу.",
        parse_mode="HTML"
    )


# ---------- Команда /gpt ----------
@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()

    if not query:
        safe_send_message(message.chat.id, "❗ Напиши текст после команды /gpt")
        return

    send_gpt_answer(message.chat.id, query)


# ===============================
#   GPT: Универсальная функция
# ===============================
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
            safe_send_message(
                chat_id,
                "⚠️ <b>Лимит OpenAI исчерпан.</b>\n"
                "Попробуй позже.",
                parse_mode="HTML"
            )
            return

        safe_send_message(chat_id, "⚠️ Ошибка. Попробуй снова позже.")


# ---------- Обработка обычных текстовых сообщений ----------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)


# ---------- Запуск бота ----------
bot.polling(none_stop=True)
