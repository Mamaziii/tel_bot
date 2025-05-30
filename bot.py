import os
import requests
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument

TOKEN = os.getenv("BOT_TOKEN")
AUDIO_TEMP_FILE = "temp_song.mp3"

# AudD API
AUDD_API_KEY = os.getenv("AUDD_API_KEY")

# Telethon credentials
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
client = TelegramClient("music_session", api_id, api_hash)
client.start()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "سلام! ویس یا ویدیو بفرست تا موزیکشو پیدا کنم 🎧 یا دستور /latest رو بفرست تا آخرین آهنگ کانال رو بفرستم!")

@bot.message_handler(commands=["latest"])
def send_latest_song(message):
    try:
        msgs = client.get_messages('bitrait_public', limit=1, filter=InputMessagesFilterDocument)
        if not msgs:
            bot.reply_to(message, "❌ فایل جدیدی پیدا نشد.")
            return

        msg = msgs[0]
        if not msg.document:
            bot.reply_to(message, "❌ پیام آخر شامل فایل صوتی نیست.")
            return

        file_path = msg.download_media()
        with open(file_path, 'rb') as f:
            bot.send_audio(message.chat.id, f, caption="🎵 آخرین آهنگ از کانال MyMusicChannel")

        os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"❌ خطا در دریافت آهنگ: {e}")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.reply_to(message, "لطفاً ویس یا ویدیو بفرست، متن فعلاً پشتیبانی نمی‌شه.")

@bot.message_handler(content_types=["voice", "video"])
def handle_media(message):
    try:
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_file = "input.mp3"
        with open(input_file, "wb") as f:
            f.write(downloaded_file)

        with open(input_file, "rb") as f:
            files = {'file': f}
            data = {
                'api_token': AUDD_API_KEY,
                'return': 'apple_music,spotify',
            }
            response = requests.post("https://api.audd.io/", data=data, files=files)
            result = response.json()

        if not result.get("result") or not result["result"].get("song_link"):
            bot.reply_to(message, "متأسفم، نتونستم آهنگ رو شناسایی کنم ❌")
            return

        song = result["result"]
        title = song["title"]
        artist = song["artist"]
        song_link = song["song_link"]

        mp3_download_link = get_mp3_download_link(f"{title} {artist}")

        if not mp3_download_link:
            bot.reply_to(message, f"✅ آهنگ شناسایی شد: {title} - {artist}\nلینک: {song_link}")
            return

        mp3_data = requests.get(mp3_download_link)
        with open(AUDIO_TEMP_FILE, "wb") as f:
            f.write(mp3_data.content)

        with open(AUDIO_TEMP_FILE, "rb") as f:
            bot.send_audio(message.chat.id, f, caption=f"{title} - {artist} 🎶")

        os.remove(AUDIO_TEMP_FILE)
        os.remove(input_file)

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

def get_mp3_download_link(query):
    try:
        response = requests.get(f"https://api-mp3juices.yt/api/search.php?q={query}")
        results = response.json()
        if results and isinstance(results, list):
            return results[0]["url"]
    except:
        pass
    return None

bot.infinity_polling()
