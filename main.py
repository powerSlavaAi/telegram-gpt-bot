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
        BotCommand("image", "Создать картинку"),
    ]
)

# ---------- Команда /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>Привет!</b>\nЯ бот на GPT. Пиши текст, отправляй картинки или используй команды.",
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
        "/image <описание> – генерация картинки\n"
        "\nПросто отправь фото — я проанализирую его."
    )

# ---------- Команда /gpt ----------
@bot.message_handler(commands=['gpt'])
def gpt_cmd(message):
    query = message.text.replace("/gpt", "").strip()

    if not query:
        bot.send_message(message.chat.id, "❗ Напиши текст после команды /gpt")
        return

    send_gpt_answer(message.chat.id, query)

# ---------- Универсальная функция ответа GPT ----------
def send_gpt_answer(chat_id, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )

        answer = response.choices[0].message.content
        bot.send_message(chat_id, answer)

    except Exception:
        bot.send_message(chat_id, "⚠️ Ошибка. Попробуй снова позже.")


# ---------- Генерация изображений /image ----------
@bot.message_handler(commands=['image'])
def image_cmd(message):
    prompt = message.text.replace("/image", "").strip()

    if not prompt:
        bot.send_message(message.chat.id, "❗ Напиши описание картинки после /image")
        return

    bot.send_message(message.chat.id, "⏳ Генерирую изображение...")

    try:
        img = client.images.generate(
            model="gpt-image-1-mini",       # бесплатная модель
            prompt=prompt,
            size="1024x1024"
        )

        image_url = img.data[0].url
        bot.send_photo(message.chat.id, image_url)

    except Exception:
        bot.send_message(message.chat.id, "⚠️ Ошибка генерации изображения.")


# ---------- Анализ изображений ----------
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    bot.send_message(message.chat.id, "🔍 Анализирую изображение...")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "image": downloaded},
                        {"type": "text", "text": "Опиши, что изображено на фото."}
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content
        bot.send_message(message.chat.id, answer)

    except Exception:
        bot.send_message(message.chat.id, "⚠️ Ошибка анализа изображения.")


# ---------- Обработка простого текста ----------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_gpt_answer(message.chat.id, message.text)

# ---------- Запуск бота ----------
bot.polling(none_stop=True)
