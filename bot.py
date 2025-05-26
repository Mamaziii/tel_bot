import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "سلام! لطفاً وویس یا ویدیو بفرست تا آهنگشو پیدا کنم 🎵")

@bot.message_handler(content_types=['voice', 'video', 'audio'])
def handle_audio(message):
    try:
        file_id = (
            message.voice.file_id if message.voice else
            message.video.file_id if message.video else
            message.audio.file_id
        )
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)

        with open("voice.mp3", "wb") as f:
            f.write(file)

        with open("voice.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": SHZ_HOST,
            "Content-Type": "text/plain"
        }

        response = requests.post(
            f"https://{SHZ_HOST}/songs/v2/detect",
            headers=headers,
            data=audio_bytes
        )

        result = response.json()

        if 'track' not in result:
            bot.send_message(message.chat.id, "متأسفم، Shazam نتونست این آهنگ رو شناسایی کنه ❌")
            return

        track = result["track"]
        title = track.get("title", "")
        subtitle = track.get("subtitle", "")
        url = track.get("url", "")

        msg = f"🎶 {title} - {subtitle}\n🌐 {url}"
        bot.send_message(message.chat.id, msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"مشکلی در تماس با Shazam پیش اومد.\n{e}")

bot.infinity_polling()
