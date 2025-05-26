import telebot
import requests
import os
import uuid

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(BOT_TOKEN)

def identify_song(file_path):
    url = "https://shazam-core.p.rapidapi.com/v1/tracks/recognize"

    with open(file_path, "rb") as file:
        files = {"upload_file": file}
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": SHZ_HOST
        }
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        data = response.json()
        if "track" in data and data["track"]:
            track = data["track"]
            title = track.get("title", "Unknown Title")
            subtitle = track.get("subtitle", "")
            link = track.get("url", "No link available")
            return f"🎵 {title} - {subtitle}\n🔗 {link}"
        else:
            return "متأسفم، نتونستم آهنگ رو شناسایی کنم."
    else:
        return "مشکلی در پردازش فایل پیش اومد!"

@bot.message_handler(content_types=['voice', 'audio', 'video', 'document'])
def handle_media(message):
    try:
        file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id if message.audio else message.video.file_id if message.video else message.document.file_id)
        file_data = bot.download_file(file_info.file_path)

        os.makedirs("downloads", exist_ok=True)
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join("downloads", filename)

        with open(file_path, "wb") as f:
            f.write(file_data)

        result = identify_song(file_path)
        bot.reply_to(message, result)

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎧 خوش آمدی! برام ویس یا ویدیو بفرست تا آهنگشو پیدا کنم.")

# شروع با Webhook یا Polling
#bot.infinity_polling()
