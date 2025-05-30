import os
import requests
import telebot
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument

# ENV config
TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_KEY = os.getenv("AUDD_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "music_session"
CHANNEL_USERNAME = "soundcloudclub"  # ← آیدی کانال بدون @

AUDIO_TEMP_FILE = "temp_song.mp3"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "سلام! یه ویس یا ویدیو بفرست تا برات موزیک کاملش رو پیدا کنم 🎧")

@bot.message_handler(commands=["latest"])
def send_latest_song(message):
    try:
        result = asyncio.run(fetch_latest_song())
        if not result:
            bot.reply_to(message, "متأسفم، آهنگی پیدا نشد ❌")
            return
        title, file_path = result
        with open(file_path, "rb") as audio:
            bot.send_audio(message.chat.id, audio, caption=f"🎶 {title}")
        os.remove(file_path)
    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت آهنگ: {e}")

async def fetch_latest_song():
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        messages = await client.get_messages(CHANNEL_USERNAME, limit=1, filter=InputMessagesFilterDocument)
        if not messages or not messages[0].file:
            return None
        msg = messages[0]
        file_name = msg.file.name or "latest_song.mp3"
        file_path = os.path.join(".", file_name)
        await msg.download_media(file=file_path)
        return file_name, file_path

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
            bot.reply_to(message, f"آهنگ شناسایی شد: {title} - {artist} 🎵\nولی نتونستم فایل رو بفرستم. لینک: {song_link}")
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
