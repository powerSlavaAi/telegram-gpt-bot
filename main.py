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

# ---------------- Команды ----------------
bot.set_my_commands(
    [
        BotCommand("start", "Запустить бота"),
        BotCommand("menu", "Открыть меню"),
        BotCommand("help", "Помощь"),
    ]
)

# ---------------- Меню ----------------
def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 GPT-ответ", callback_data="ask_gpt"),
        types.InlineKeyboardButton("🎤 Голосовой ответ", callback_data="voice_reply")
    )
    markup.add(
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
    )
    bot.send_message(chat_id, "<b>Выберите действие:</b>", reply_markup=markup)


# ---------------- /start ----------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "<b>Привет!</b> Я бот на GPT-4o-mini.\nМогу понимать текст и голос, и отвечать тоже голосом."
    )
    send_main_menu(message.chat.id)


# ---------------- /menu ----------------
@bot.message_handler(commands=['menu'])
def menu(message):
    send_main_menu(message.chat.id)


# ---------------- /help ----------------
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📌 <b>Доступные команды:</b>\n"
        "/start – запуск\n"
        "/menu – открыть меню\n"
        "/help – помощь\n\n"
        "Отправь мне текст или голос, и я отвечу."
    )


# ---------------- Inline-menu обработка ----------------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "ask_gpt":
        bot.send_message(call.message.chat.id, "💬 Напиши вопрос для GPT.")
    elif call.data == "voice_reply":
        bot.send_message(call.message.chat.id, "🎤 Отправь голосовое сообщение.")
    elif call.data == "help":
        help_cmd(call.message)
    elif call.data == "settings":
        bot.send_message(call.message.chat.id, "⚙️ Настройки пока недоступны.")


# ---------------- Текстовые сообщения ----------------
@bot.message_handler(func=lambda m: m.content_type == "text")
def handle_text(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response.choices[0].message.content

        # --- Генерация голосового ответа ---
        tts_voice = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=answer
        )

        voice_path = "answer.ogg"
        with open(voice_path, "wb") as f:
            f.write(tts_voice.read())

        bot.send_message(message.chat.id, answer)
        bot.send_voice(message.chat.id, open(voice_path, "rb"))

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "insufficient_quota" in error_text:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Лимит OpenAI исчерпан.</b> Попробуй позже."
            )
            return

        bot.send_message(message.chat.id, "⚠️ Ошибка. Попробуй ещё раз.")


# ---------------- Голосовые сообщения ----------------
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # скачиваем файл
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        # --- Распознаём речь ---
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=("voice.ogg", downloaded)
        )

        user_text = transcription.text

        # --- GPT-ответ ---
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_text}]
        )

        answer = response.choices[0].message.content

        # --- Генерируем голосовой ответ ---
        tts_voice = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=answer
        )

        voice_path = "answer.ogg"
        with open(voice_path, "wb") as f:
            f.write(tts_voice.read())

        bot.send_message(message.chat.id, f"🗣 Ты сказал: <i>{user_text}</i>")
        bot.send_voice(message.chat.id, open(voice_path, "rb"))

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "insufficient_quota" in error_text:
            bot.send_message(
                message.chat.id,
                "⚠️ Квота OpenAI закончилась. Попробуй позже."
            )
            return

        bot.send_message(message.chat.id, "⚠️ Ошибка обработки голоса.")

# ---------------- Запуск ----------------
bot.polling(none_stop=True)
