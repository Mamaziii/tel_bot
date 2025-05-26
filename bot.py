import os
import requests
import telebot
import subprocess

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(TOKEN)

# تبدیل فایل صوتی به wav (برای ارسال به Shazam)
def convert_to_wav(input_file, output_file="voice.wav"):
    subprocess.run(["ffmpeg", "-y", "-i", input_file, "-ar", "44100", "-ac", "2", output_file])

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "سلام! یه وویس یا ویدیو بفرست تا آهنگشو پیدا کنم 🎧")

@bot.message_handler(content_types=['voice', 'audio', 'video', 'document'])
def handle_media(message):
    try:
        file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id if message.audio else message.video.file_id if message.video else message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("voice.ogg", 'wb') as new_file:
            new_file.write(downloaded_file)

        convert_to_wav("voice.ogg", "voice.wav")

        with open("voice.wav", "rb") as f:
            data = f.read()

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": SHZ_HOST,
            "content-type": "text/plain"
        }

        response = requests.post(
            f"https://{SHZ_HOST}/songs/v2/detect",
            headers=headers,
            data=data
        )

        result = response.json()

        # ✅ بررسی اینکه آیا track پیدا شده یا نه
        if 'track' not in result:
            bot.send_message(message.chat.id, "متأسفم، Shazam نتونست این آهنگ رو شناسایی کنه ❌")
            return

        track = result['track']
        title = track.get('title', 'نامشخص')
        subtitle = track.get('subtitle', '')
        url = track.get('url', 'بدون لینک')

        msg = f"🎶 {title} - {subtitle}\n🌐 {url}"
        bot.send_message(message.chat.id, msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"خطا در پردازش: {e}")

bot.infinity_polling()
