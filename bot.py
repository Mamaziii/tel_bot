import os
import requests
from telethon.sync import TelegramClient
from telethon.tl.types import Document
from telebot import TeleBot, types

# تلگرام بات
bot_token = os.getenv("BOT_TOKEN")
audd_api_key = os.getenv("AUDD_API_KEY")
bot = TeleBot(bot_token)

# Telethon client
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
telethon_client = TelegramClient("music_session", api_id, api_hash)
telethon_client.start()

# آیدی کانال عمومی موزیک
MUSIC_CHANNEL = "soundcloudclub"  # بدون @

DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.reply_to(message, "سلام! ویس، ویدیو یا اسم آهنگ رو بفرست تا پیداش کنم 🎵")

@bot.message_handler(content_types=["voice", "video"])
def handle_voice_or_video(message):
    try:
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        input_path = os.path.join(DOWNLOADS_FOLDER, "input.mp3")
        with open(input_path, "wb") as f:
            f.write(downloaded)

        with open(input_path, "rb") as f:
            data = {
                'api_token': audd_api_key,
                'return': 'apple_music,spotify',
            }
            response = requests.post("https://api.audd.io/", data=data, files={"file": f})
            result = response.json()

        if not result.get("result"):
            bot.reply_to(message, "متأسفم، نتونستم آهنگ رو شناسایی کنم ❌")
            return

        title = result["result"]["title"]
        artist = result["result"]["artist"]
        query = f"{title} {artist}"

        send_song_from_channel(query, message.chat.id, f"🎶 {title} - {artist}")

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

@bot.message_handler(content_types=["text"])
def handle_text_query(message):
    query = message.text.strip()
    if not query:
        bot.reply_to(message, "لطفاً اسم آهنگ یا خواننده رو بفرست.")
        return

    try:
        send_song_from_channel(query, message.chat.id, f"🔍 جستجو: {query}")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

def send_song_from_channel(query, chat_id, caption):
    try:
        with telethon_client:
            messages = telethon_client.iter_messages(MUSIC_CHANNEL, search=query, limit=10)
            for msg in messages:
                if msg.media and isinstance(msg.media, Document) and msg.file.mime_type == "audio/mpeg":
                    file_path = os.path.join(DOWNLOADS_FOLDER, f"{msg.id}.mp3")
                    telethon_client.download_media(msg, file_path)

                    with open(file_path, "rb") as audio:
                        bot.send_audio(chat_id, audio, caption=caption)
                    os.remove(file_path)
                    return

        bot.send_message(chat_id, "آهنگ پیدا نشد ❌")

    except Exception as e:
        bot.send_message(chat_id, f"خطا در دریافت آهنگ: {e}")

bot.infinity_polling()
