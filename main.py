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


# ---------- Генерация inline-кнопок ----------
def build_buttons():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔄 Пересформулировать", callback_data="retry"),
    )
    kb.row(
        types.InlineKeyboardButton("➡️ Продолжить", callback_data="continue"),
        types.InlineKeyboardButton("🗑 Удалить", callback_data="delete_msg"),
    )
    kb.add(
        types.InlineKeyboardButton("✨ Новое сообщение", callback_data="new")
    )
    return kb


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
            answer,
            reply_markup=build_buttons()   # ← Inline-кнопки здесь
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


# ---------- Обработка inline-кнопок ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "retry":
        bot.answer_callback_query(call.id, "Пересформулирую…")
        msg = call.message.text
        send_retry(call.message)

    elif call.data == "continue":
        bot.answer_callback_query(call.id, "Пишу продолжение…")
        send_continue(call.message)

    elif call.data == "new":
        bot.answer_callback_query(call.id, "Жду новое сообщение ✨")
        bot.send_message(call.message.chat.id, "Напиши новое сообщение:")

    elif call.data == "delete_msg":
        bot.answer_callback_query(call.id, "Удалено")
        bot.delete_message(call.message.chat.id, call.message.message_id)


# ---------- Логика кнопок ----------
def send_retry(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Пересформулируй: " + message.text}]
    )
    bot.send_message(
        message.chat.id,
        response.choices[0].message.content,
        reply_markup=build_buttons()
    )


def send_continue(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Продолжи этот текст: " + message.text}
        ]
    )
    bot.send_message(
        message.chat.id,
        response.choices[0].message.content,
        reply_markup=build_buttons()
    )


bot.polling(none_stop=True)
