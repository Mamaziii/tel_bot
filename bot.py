import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

HEADERS = {
    "User-Agent": "okhttp/4.2.2",
    "Accept": "application/json",
    "Connection": "keep-alive"
}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "سلام! اسم آهنگ یا خواننده رو بفرست تا فایل کاملشو بفرستم 🎵")

@bot.message_handler(content_types=['text'])
def search_melobit(message):
    query = message.text.strip()
    try:
        url = f"https://melobit.com/api/v1/search/query/{query}"
        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            bot.send_message(message.chat.id, f"خطا در اتصال به Melobit ❌\nوضعیت: {res.status_code}")
            return

        data = res.json()
        songs = data.get("songs")
        if not songs:
            bot.send_message(message.chat.id, "آهنگی پیدا نشد ❌")
            return

        song = songs[0]
        title = song["title"]
        artist = song["artists"][0]["fullName"]
        audio_url = song["audio"]["high"]["url"]

        caption = f"🎶 {title} - {artist}"
        bot.send_audio(message.chat.id, audio=audio_url, caption=caption)

    except Exception as e:
        bot.send_message(message.chat.id, f"خطایی رخ داد:\n{e}")

bot.infinity_polling()
