import os
import requests
import telebot
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import Search
from telethon.tl.types import InputMessagesFilterMusic

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_KEY = os.getenv("AUDD_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_USERNAME = "@your_channel_username"  # ← آیدی کانال عمومی

bot = telebot.TeleBot(BOT_TOKEN)

# راه‌اندازی کلاینت Telethon
telethon_client = TelegramClient("music_session", API_ID, API_HASH)
telethon_client.start()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
AUDIO_TEMP_FILE = os.path.join(DOWNLOAD_DIR, "temp_song.mp3")

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "🎧 سلام! ویس یا ویدیو بفرست، یا اسم آهنگ یا خواننده رو تایپ کن تا موزیک کاملشو برات بیارم.")

@bot.message_handler(content_types=["voice", "video"])
def handle_media(message):
    try:
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_file = os.path.join(DOWNLOAD_DIR, "input.mp3")
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

        if not result.get("result") or not result["result"].get("title"):
            bot.reply_to(message, "❌ متأسفم، نتونستم آهنگ رو شناسایی کنم.")
            return

        song = result["result"]
        title = song["title"]
        artist = song["artist"]
        search_query = f"{title} {artist}"

        # جستجو در کانال
        music_file = search_music_in_channel(search_query)
        if music_file:
            with open(music_file, "rb") as f:
                bot.send_audio(message.chat.id, f, caption=f"🎶 {title} - {artist}")
            os.remove(music_file)
        else:
            song_link = song.get("song_link", "لینک: نداره")
            bot.reply_to(message, f"🎧 آهنگ شناسایی شد: \n{title} - {artist}\n({song_link})")

        os.remove(input_file)

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    query = message.text.strip().lower()
    if not query:
        bot.reply_to(message, "لطفاً اسم خواننده یا آهنگ رو بنویس 🎵")
        return

    bot.reply_to(message, "🔎 در حال جستجو در کانال موزیک...")

    try:
        music_file = search_music_in_channel(query)
        if music_file:
            with open(music_file, "rb") as f:
                bot.send_audio(message.chat.id, f, caption=f"🎶 نتیجه برای: {query}")
            os.remove(music_file)
        else:
            bot.reply_to(message, "❌ متأسفم، آهنگی با این عنوان در کانال پیدا نشد.")

    except Exception as e:
        bot.reply_to(message, f"خطا در جستجو: {e}")

def search_music_in_channel(query):
    try:
        result = telethon_client.loop.run_until_complete(
            telethon_client(Search(
                peer=CHANNEL_USERNAME,
                q=query,
                filter=InputMessagesFilterMusic(),
                limit=1
            ))
        )

        if result and result.messages:
            msg = result.messages[0]
            return telethon_client.loop.run_until_complete(
                msg.download_media(file=DOWNLOAD_DIR)
            )
    except Exception as e:
        print(f"خطا در جستجوی کانال: {e}")
    return None

bot.infinity_polling()
