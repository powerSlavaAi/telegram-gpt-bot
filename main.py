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


# ---------- Команда /help ----------
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "<b>Доступные команды:</b>\n"
        "/start – запуск бота\n"
        "/help – помощь\n"
        "/gpt <текст> – задать вопрос ChatGPT\n"
        "\nПросто напиши любое сообщение, и я отвечу."
    )


# ---------- Команда /gpt ----------
@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()

    if not query:
        bot.send_message(message.chat.id, "❗ Напиши текст после команды /gpt")
        return

    send_gpt_answer(message.chat.id, query)


# ---------- Универсальная функция запроса к GPT ----------
def send_gpt_answer(chat_id, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )

        answer = response.choices[0].message.content
        bot.send_message(chat_id, answer)

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "insufficient_quota" in error_text:
            bot.send_message(
                chat_id,
                "⚠️ <b>Лимит OpenAI исчерпан.</b>\n"
                "Текстовые запросы стоят мало — попробуй чуть позже."
            )
            return

        bot.send_message(chat_id, "⚠️ Ошибка. Попробуй снова позже.")


# ---------- Обработка обычных текстовых сообщений ----------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)


# ---------- ВАЖНО: голос отключён полностью ----------
# @bot.message_handler(content_types=['voice'])
# def handle_voice(message):
#     pass  # Отключено — чтобы не тратить квоту OpenAI


# ---------- Запуск бота ----------
bot.polling(none_stop=True)
