import os
import uuid
import telebot
import requests

# خواندن توکن‌ها از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(BOT_TOKEN)

def recognize_song(file_path):
    try:
        url = "https://shazam-core.p.rapidapi.com/v1/tracks/recognize"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": SHZ_HOST
        }

        with open(file_path, 'rb') as f:
            files = {"upload_file": f}
            response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            data = response.json()
            track = data.get("track")
            if track:
                title = track.get("title", "Unknown Title")
                subtitle = track.get("subtitle", "")
                url = track.get("url", "")
                return f"🎵 {title} - {subtitle}\n🔗 {url}"
            else:
                return "متأسفم، نتونستم آهنگ رو شناسایی کنم."
        else:
            return "مشکلی در تماس با Shazam پیش اومد."
    except Exception as e:
        return f"خطا در پردازش: {e}"

def download_file_from_message(message):
    if message.voice:
        file_id = message.voice.file_id
        ext = ".ogg"
    elif message.audio:
        file_id = message.audio.file_id
        ext = ".mp3"
    elif message.video:
        file_id = message.video.file_id
        ext = ".mp4"
    elif message.document:
        file_id = message.document.file_id
        ext = os.path.splitext(message.document.file_name)[1]
    else:
        return None

    file_info = bot.get_file(file_id)
    file_data = bot.download_file(file_info.file_path)

    os.makedirs("downloads", exist_ok=True)
    unique_filename = str(uuid.uuid4()) + ext
    file_path = os.path.join("downloads", unique_filename)

    with open(file_path, "wb") as f:
        f.write(file_data)

    return file_path

@bot.message_handler(content_types=['voice', 'audio', 'video', 'document'])
def handle_media(message):
    msg = bot.reply_to(message, "⏳ در حال شناسایی آهنگ...")
    try:
        file_path = download_file_from_message(message)
        if not file_path:
            bot.edit_message_text("نوع فایل پشتیبانی نمی‌شود.", message.chat.id, msg.message_id)
            return

        result = recognize_song(file_path)
        bot.edit_message_text(result, message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"مشکلی در پردازش فایل پیش اومد!\n{str(e)}", message.chat.id, msg.message_id)
    finally:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "🎶 سلام! ویس یا ویدیو بفرست تا آهنگشو پیدا کنم.")

bot.infinity_polling()
