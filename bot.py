import os
import requests
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
import asyncio

TOKEN = os.getenv("BOT_TOKEN")
AUDIO_TEMP_FILE = "temp_song.mp3"
CHANNEL_USERNAME = os.getenv("soundcloudclub")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = telebot.TeleBot(TOKEN)

# بررسی و ساخت فولدر دانلود
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "سلام! یه ویس، ویدیو یا اسم آهنگ بفرست تا برات موزیکشو پیدا کنم 🎧")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    query = message.text.strip()

    # تلاش برای شناسایی از AudD
    audd_result = search_with_audd(query)
    if audd_result:
        bot.reply_to(message, audd_result)
        return

    # اگر AudD پیدا نکرد => جستجو در کانال تلگرام
    bot.reply_to(message, "🔎 در حال جستجو در کانال برای: " + query)

    result = asyncio.run(search_in_channel(query))
    if result and result.document:
        file_name = result.document.attributes[0].file_name if result.document.attributes else "music.mp3"
        file_path = f"downloads/{file_name}"
        result.download_media(file_path)

        with open(file_path, "rb") as f:
            bot.send_audio(message.chat.id, f, caption=f"🎶 {file_name}")
        os.remove(file_path)
    else:
        bot.reply_to(message, "متأسفم، آهنگ پیدا نشد ❌")

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
                'api_token': os.getenv("AUDD_API_KEY"),
                'return': 'apple_music,spotify',
            }
            response = requests.post("https://api.audd.io/", data=data, files=files)
            result = response.json()

        if not result.get("result") or not result["result"].get("song_link"):
            bot.reply_to(message, "نتونستم آهنگ رو شناسایی کنم ❌")
            return

        song = result["result"]
        title = song["title"]
        artist = song["artist"]
        song_link = song["song_link"]

        mp3_download_link = get_mp3_download_link(f"{title} {artist}")
        if not mp3_download_link:
            bot.reply_to(message, f"آهنگ شناسایی شد: {title} - {artist} 🎵\nولی لینک دانلود نشد: {song_link}")
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

def search_with_audd(query):
    try:
        data = {
            'api_token': os.getenv("AUDD_API_KEY"),
            'q': query,
            'return': 'apple_music,spotify',
        }
        response = requests.post("https://api.audd.io/findLyrics/", data=data)
        result = response.json()

        if result.get("result") and len(result["result"]) > 0:
            song = result["result"][0]
            return f"🎵 آهنگ شناسایی شد:\n{song['title']} - {song['artist']}\nلینک: {song.get('song_link', 'نداره')}"
    except:
        pass
    return None

async def search_in_channel(query):
    try:
        async with TelegramClient("music_session", API_ID, API_HASH) as client:
            messages = await client.get_messages(
                CHANNEL_USERNAME, 
                limit=100, 
                filter=InputMessagesFilterDocument
            )
            for msg in messages:
                if msg.message and query.lower() in msg.message.lower():
                    return msg
    except Exception as e:
        print(f"[❌] خطا در جستجوی کانال: {e}")
    return None

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
