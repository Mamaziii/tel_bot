import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
AUDIO_TEMP_FILE = "temp_song.mp3"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "سلام! یه ویس یا ویدیو بفرست تا برات موزیک کاملش رو پیدا کنم 🎧")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.reply_to(message, "لطفاً ویس یا ویدیو بفرست، متن فعلاً پشتیبانی نمی‌شه.")

@bot.message_handler(content_types=["voice", "video"])
def handle_media(message):
    try:
        # دریافت فایل از تلگرام
        file_id = message.voice.file_id if message.voice else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # ذخیره فایل
        input_file = "input.mp3"
        with open(input_file, "wb") as f:
            f.write(downloaded_file)

        # ارسال فایل به AudD
        with open(input_file, "rb") as f:
            files = {'file': f}
            data = {
                'api_token': os.getenv("AUDD_API_KEY"),
                'return': 'apple_music,spotify',
            }
            response = requests.post("https://api.audd.io/", data=data, files=files)
            result = response.json()

        # بررسی نتیجه
        if not result.get("result") or not result["result"].get("song_link"):
            bot.reply_to(message, "متأسفم، نتونستم آهنگ رو شناسایی کنم ❌")
            return

        song = result["result"]
        title = song["title"]
        artist = song["artist"]
        song_link = song["song_link"]

        # استفاده از mp3juices API یا هر منبع دیگری برای دریافت لینک مستقیم MP3
        mp3_download_link = get_mp3_download_link(f"{title} {artist}")

        if not mp3_download_link:
            bot.reply_to(message, f"آهنگ شناسایی شد: {title} - {artist} 🎵\nولی نتونستم فایل رو بفرستم. لینک: {song_link}")
            return

        # دانلود MP3
        mp3_data = requests.get(mp3_download_link)
        with open(AUDIO_TEMP_FILE, "wb") as f:
            f.write(mp3_data.content)

        # ارسال فایل به کاربر
        with open(AUDIO_TEMP_FILE, "rb") as f:
            bot.send_audio(message.chat.id, f, caption=f"{title} - {artist} 🎶")

        # پاک‌سازی فایل‌ها
        os.remove(AUDIO_TEMP_FILE)
        os.remove(input_file)

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

def get_mp3_download_link(query):
    try:
        response = requests.get(f"https://api-mp3juices.yt/api/search.php?q={query}")
        results = response.json()
        if results and isinstance(results, list):
            return results[0]["url"]  # اولین لینک مستقیم mp3
    except:
        pass
    return None

bot.infinity_polling()
