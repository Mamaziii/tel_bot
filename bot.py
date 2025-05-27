import os
import subprocess
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = "shazam.p.rapidapi.com"

bot = telebot.TeleBot(TOKEN)

def convert_to_mp3(input_file, output_file, message):
    subprocess.run(["ffmpeg", "-y", "-i", input_file, output_file])
    if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
        bot.reply_to(message, "⚠️ تبدیل به mp3 موفق نبود یا فایل خالیه.")
        return False
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! یه ویس یا ویدیو بفرست تا شازمش کنم 🎵")

@bot.message_handler(content_types=['voice', 'audio', 'video'])
def handle_audio(message):
    try:
        file_id = None
        if message.voice:
            file_id = message.voice.file_id
            input_ext = '.ogg'
        elif message.video:
            file_id = message.video.file_id
            input_ext = '.mp4'
        elif message.audio:
            file_id = message.audio.file_id
            input_ext = '.mp3'
        else:
            bot.reply_to(message, "❌ فایل صوتی/ویس/ویدیو پشتیبانی نمی‌شود.")
            return

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_file = "input" + input_ext
        output_file = "voice.mp3"

        with open(input_file, 'wb') as f:
            f.write(downloaded_file)

        if not convert_to_mp3(input_file, output_file, message):
            return

        # ارسال فایل mp3 به شازم
        with open(output_file, 'rb') as f:
            files = {'file': f}
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": SHZ_HOST
            }
            response = requests.post(
                "https://shazam.p.rapidapi.com/songs/detect",
                files=files,
                headers=headers
            )

        if response.status_code != 200:
            bot.reply_to(message, f"❌ Shazam پاسخ نداد. وضعیت: {response.status_code}")
            return

        data = response.json()
        track = data.get("track")
        if not track:
            bot.reply_to(message, "متأسفم، Shazam نتونست این آهنگ رو شناسایی کنه ❌")
            return

        title = track["title"]
        subtitle = track["subtitle"]
        url = track["url"]
        bot.reply_to(message, f"🎵 {title} - {subtitle}\n🔗 {url}")

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

bot.infinity_polling()
