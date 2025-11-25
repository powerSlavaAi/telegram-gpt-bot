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

# ------------------- Голосовые сообщения -------------------
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # 1. Скачиваем аудио
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        voice_path = "voice.ogg"
        with open(voice_path, "wb") as f:
            f.write(downloaded_file)

        # 2. Распознаём речь (Whisper)
        with open(voice_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="gpt-4o-mini-tts",  # Whisper
                response_format="text"
            )

        text = transcript

        bot.send_message(
            message.chat.id,
            f"<b>🎤 Вы сказали:</b> {text}"
        )

        # 3. GPT отвечает текстом
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )

        answer = response.choices[0].message.content

        bot.send_message(
            message.chat.id,
            answer
        )

        # 4. Генерация голосового ответа
        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=answer
        )

        audio_path = "answer.ogg"
        with open(audio_path, "wb") as f:
            f.write(tts)

        # 5. Отправка голосового ответа
        with open(audio_path, "rb") as audio:
            bot.send_voice(message.chat.id, audio)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка обработки голоса: <code>{e}</code>")

# ------------------- Текстовые сообщения -------------------
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
            answer
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

# ------------------- Запуск -------------------
bot.polling(none_stop=True)
