import os
import requests
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument

# Bot Token & AudD Key
TOKEN = os.getenv("BOT_TOKEN")
AUDD_KEY = os.getenv("AUDD_API_KEY")

# Telethon credentials
API_ID = int(os.getenv("API_ID"))         # از my.telegram.org بگیر
API_HASH = os.getenv("API_HASH")          # از my.telegram.org بگیر
MUSIC_CHANNEL = "AhangeJadid"             # کانال عمومی‌ای که آهنگ‌ها توشه

# TeleBot
bot = telebot.TeleBot(TOKEN)
AUDIO_TEMP_FILE = "temp_song.mp3"

# Telethon client
client = TelegramClient("music_session", API_ID, API_HASH)

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "سلام! یه ویس یا ویدیو بفرست تا آهنگش رو برات بیارم 🎧")

@bot.message_handler(content_types=["voice", "video"])
def handle_media(message):
    try:
        # فایل ورودی رو دریافت کن
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file = "input.mp3"

        with open(input_file, "wb") as f:
            f.write(downloaded_file)

        # ارسال به AudD
        with open(input_file, "rb") as f:
            files = {'file': f}
            data = {'api_token': AUDD_KEY, 'return': 'apple_music,spotify'}
            response = requests.post("https://api.audd.io/", data=data, files=files)
            result = response.json()

        if not result.get("result") or not result["result"].get("title"):
            bot.reply_to(message, "نتونستم آهنگ رو شناسایی کنم ❌")
            return

        title = result["result"]["title"]
        artist = result["result"]["artist"]
        search_query = f"{title} {artist}"

        # جستجو در کانال تلگرام با Telethon
        with client:
            messages = client.iter_messages(MUSIC_CHANNEL, search=title)
            for msg in messages:
                if msg.media and isinstance(msg.media, MessageMediaDocument):
                    file_path = f"./downloads/{msg.file.name}"
                    msg.download_media(file_path)
                    with open(file_path, "rb") as f:
                        bot.send_audio(message.chat.id, f, caption=f"{title} - {artist} 🎶")
                    os.remove(file_path)
                    os.remove(input_file)
                    return

        # اگه چیزی پیدا نشد
        bot.reply_to(message, f"آهنگ شناسایی شد: {title} - {artist} ولی در کانال پیدا نشد 🔍")

    except Exception as e:
        bot.reply_to(message, f"❌ خطا در پردازش: {e}")

bot.infinity_polling()
