import os
import telebot
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Включаем HTML формат сообщений
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>Привет!</b> Я бот на GPT. Напиши мне что-нибудь!"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message.text}]
        )

        answer = response.choices[0].message.content

        # 🔥 Премиальное HTML-оформление
        formatted = f"""
<b>🔍 Анализ:</b>

<blockquote>
{answer}
</blockquote>

<b>💡 Вывод:</b>
<i>Если хочешь — могу рассказать подробнее или разобрать тему глубже.</i>
"""

        bot.send_message(message.chat.id, formatted)

    except Exception as e:
        error_text = str(e)

        # Обработка ошибки 429
        if "429" in error_text or "rate_limit" in error_text:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Превышен лимит запросов к OpenAI.</b>\nПодожди 20–30 секунд и попробуй снова."
            )
            return

        bot.send_message(message.chat.id, f"<i>Ошибка:</i> <code>{e}</code>")

# Запуск бота
bot.polling(none_stop=True)
