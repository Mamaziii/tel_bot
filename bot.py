import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "سلام! اسم آهنگ یا خواننده رو بفرست تا فایل کاملشو بفرستم 🎵")

@bot.message_handler(content_types=['text'])
def search_melobit(message):
    query = message.text
    try:
        url = f"https://www.melobit.com/search/query/{query}"
        res = requests.get(url)

        if res.status_code != 200:
            bot.send_message(message.chat.id, f"خطا در اتصال به Melobit ❌\nوضعیت: {res.status_code}")
            return

        if not res.text.strip():
            bot.send_message(message.chat.id, "پاسخ خالی از سرور دریافت شد ❌")
            return

        try:
            json_data = res.json()
        except Exception as e:
            bot.send_message(message.chat.id, f"خطا در تبدیل پاسخ به JSON ❌\n{e}")
            return

        if not json_data.get("songs"):
            bot.send_message(message.chat.id, "متأسفم، چیزی پیدا نکردم ❌")
            return

        song = json_data["songs"][0]
        title = song["title"]
        artist = song["artists"][0]["fullName"]
        audio_url = song["audio"]["high"]["url"]

        caption = f"🎶 {title} - {artist}"
        bot.send_audio(message.chat.id, audio=audio_url, caption=caption)

    except Exception as e:
        bot.send_message(message.chat.id, f"خطایی رخ داد:\n{e}")

bot.infinity_polling()
