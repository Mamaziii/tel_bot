import os
import requests
import telebot
import subprocess
import uuid

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_KEY = os.getenv("AUDD_API_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

def convert_to_mp3(input_file, output_file):
    subprocess.run(["ffmpeg", "-y", "-i", input_file, output_file])

def search_youtube_and_get_mp3_url(query):
    search_command = f"yt-dlp -f bestaudio --extract-audio --audio-format mp3 --audio-quality 0 --get-url \"ytsearch1:{query}\""
    result = subprocess.run(search_command, shell=True, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎵 خوش اومدی! یه ویس یا ویدیو بفرست تا موزیکش رو پیدا کنم و فایل کاملشو بفرستم.")

@bot.message_handler(content_types=['voice', 'audio', 'video'])
def handle_media(message):
    try:
        file_id = message.voice.file_id if message.voice else message.audio.file_id if message.audio else message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_ext = '.ogg' if message.voice else '.mp4'
        input_file = f"input_{uuid.uuid4()}{input_ext}"
        output_file = f"output_{uuid.uuid4()}.mp3"

        with open(input_file, 'wb') as f:
            f.write(downloaded_file)

        convert_to_mp3(input_file, output_file)

        with open(output_file, 'rb') as f:
            files = {'file': f}
            data = {'api_token': AUDD_API_KEY, 'return': 'timecode,deezer,spotify'}
            response = requests.post("https://api.audd.io/", data=data, files=files)

        os.remove(input_file)
        os.remove(output_file)

        result = response.json()
        if 'result' not in result or not result['result']:
            bot.reply_to(message, "❌ متأسفم، audD نتونست آهنگ رو شناسایی کنه.")
            return

        title = result['result']['title']
        artist = result['result']['artist']
        query = f"{title} {artist}"

        mp3_url = search_youtube_and_get_mp3_url(query)
        if mp3_url:
            bot.send_audio(message.chat.id, audio=mp3_url, caption=f"🎶 {title} - {artist}")
        else:
            bot.reply_to(message, f"✅ آهنگ شناسایی شد: {title} - {artist}\nولی لینک دانلود مستقیم پیدا نشد.")

    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش: {e}")

bot.infinity_polling()
