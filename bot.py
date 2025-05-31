import os
import requests
from telebot import TeleBot, types
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument

TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_KEY = os.getenv("AUDD_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_USERNAME = os.getenv("MUSIC_CHANNEL")

bot = TeleBot(TOKEN)
telethon_client = TelegramClient("music_session", API_ID, API_HASH)
telethon_client.start()

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "سلام! 🎵 یه ویس، ویدیو یا اسم آهنگ بفرست تا موزیک کاملش رو پیدا کنم.")

@bot.message_handler(content_types=["voice", "video"])
def handle_media(message):
    file_id = message.voice.file_id if message.voice else message.video.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_path = os.path.join(DOWNLOAD_DIR, "input.mp3")
    with open(input_path, "wb") as f:
        f.write(downloaded_file)

    with open(input_path, "rb") as f:
        response = requests.post("https://api.audd.io/", data={
            'api_token': AUDD_API_KEY,
            'return': 'apple_music,spotify',
        }, files={'file': f})

    result = response.json().get("result")
    if not result:
        bot.reply_to(message, "نتونستم آهنگ رو شناسایی کنم ❌")
        return

    title = result.get("title", "")
    artist = result.get("artist", "")
    full_query = f"{title} - {artist}"

    # ابتدا تلاش با AudD
    mp3_link = result.get("song_link")
    if not mp3_link:
        # تلاش برای پیدا کردن فایل در کانال
        file_path = search_and_download_from_channel(full_query)
        if file_path:
            with open(file_path, "rb") as audio_file:
                bot.send_audio(message.chat.id, audio_file, caption=full_query)
            os.remove(file_path)
        else:
            bot.reply_to(message, f"آهنگ شناسایی شد: {full_query}\nولی پیدا نشد 📭")
        return

    bot.reply_to(message, f"آهنگ شناسایی شد: {full_query}\nلینک: {mp3_link}")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    query = message.text.strip()

    # ابتدا AudD
    response = requests.post("https://api.audd.io/", data={
        'api_token': AUDD_API_KEY,
        'q': query,
        'return': 'apple_music,spotify',
    })

    result = response.json().get("result")
    if result and result.get("song_link"):
        title = result.get("title", "")
        artist = result.get("artist", "")
        full_query = f"{title} - {artist}"
        bot.reply_to(message, f"آهنگ شناسایی شد: {full_query}\nلینک: {result['song_link']}")
        return

    # اگر AudD جواب نداد → تلاش با کانال
    file_path = search_and_download_from_channel(query)
    if file_path:
        with open(file_path, "rb") as audio_file:
            bot.send_audio(message.chat.id, audio_file, caption=query)
        os.remove(file_path)
    else:
        bot.reply_to(message, "آهنگ پیدا نشد 😞")

def search_and_download_from_channel(query):
    for message in telethon_client.iter_messages(CHANNEL_USERNAME, search=query, limit=10):
        if isinstance(message.media, MessageMediaDocument) and message.file.mime_type == "audio/mpeg":
            file_path = os.path.join(DOWNLOAD_DIR, f"{message.id}.mp3")
            telethon_client.download_media(message, file_path)
            return file_path
    return None

bot.infinity_polling()
