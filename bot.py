import os
import asyncio
import requests
from telebot import TeleBot, types
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument

# متغیرهای محیطی
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_KEY = os.getenv("AUDD_API_KEY")
CHANNEL_USERNAME = os.getenv("@bitrait_public")  # مثلاً @YourMusicChannel

# فایل موقت برای ذخیره آهنگ
AUDIO_TEMP_FILE = "downloads/temp_song.mp3"
INPUT_FILE = "downloads/input.mp3"

# ایجاد بات تلگرام
bot = TeleBot(BOT_TOKEN)

# کلاینت Telethon
telethon_client = TelegramClient("music_session", API_ID, API_HASH)
telethon_client.start()

# Helper برای اجرای توابع async در telebot
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# شروع ربات
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "سلام! 🎵 ویدیو یا ویس بفرست یا اسم آهنگ رو بنویس تا پیداش کنم.")

# دریافت ویس یا ویدیو و ارسال فایل موزیک
@bot.message_handler(content_types=["voice", "video"])
def handle_audio(message):
    try:
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(INPUT_FILE, "wb") as f:
            f.write(downloaded_file)

        with open(INPUT_FILE, "rb") as f:
            files = {'file': f}
            data = {
                'api_token': AUDD_API_KEY,
                'return': 'apple_music,spotify',
            }
            response = requests.post("https://api.audd.io/", data=data, files=files)
            result = response.json()

        if not result.get("result") or not result["result"].get("title"):
            bot.reply_to(message, "متأسفم، نتونستم آهنگ رو شناسایی کنم ❌")
            return

        title = result["result"]["title"]
        artist = result["result"]["artist"]
        query = f"{title} {artist}"

        found = run_async(search_in_channel(query))
        if found:
            with open(found, "rb") as f:
                bot.send_audio(message.chat.id, f, caption=f"{title} - {artist} 🎶")
        else:
            bot.reply_to(message, f"آهنگ شناسایی شد:\n{title} - {artist}\n(لینک: {result['result'].get('song_link', 'نداره')})")

        if os.path.exists(INPUT_FILE):
            os.remove(INPUT_FILE)
        if os.path.exists(AUDIO_TEMP_FILE):
            os.remove(AUDIO_TEMP_FILE)

    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت آهنگ: {e}")

# دریافت پیام متنی (نام آهنگ یا خواننده)
@bot.message_handler(content_types=["text"])
def handle_text(message):
    query = message.text.strip()
    found = run_async(search_in_channel(query))
    if found:
        with open(found, "rb") as f:
            bot.send_audio(message.chat.id, f, caption=f"{query} 🎶")
        os.remove(found)
    else:
        bot.reply_to(message, "متأسفم، نتونستم آهنگ رو پیدا کنم ❌")

# تابع async برای جستجو در کانال
async def search_in_channel(query):
    try:
        async for message in telethon_client.iter_messages(CHANNEL_USERNAME, limit=30, filter=InputMessagesFilterDocument):
            if message.file and query.lower() in message.text.lower():
                path = AUDIO_TEMP_FILE
                await message.download_media(file=path)
                return path
    except Exception as e:
        print(f"Search error: {e}")
    return None

# شروع ربات
bot.infinity_polling()
