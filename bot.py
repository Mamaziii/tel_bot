import os
import requests
import telebot
import subprocess
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(TOKEN)

def convert_to_mp3(input_file, output_file):
    subprocess.run(["ffmpeg", "-y", "-i", input_file, output_file])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! یه ویس یا ویدیو بفرست تا شازمش کنم 🎵")

@bot.message_handler(content_types=['voice', 'audio', 'video'])
def handle_audio(message):
    try:
        file_info = bot.get_file(message.voice.file_id if message.voice else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_ext = '.ogg' if message.voice else '.mp4'
        input_file = "input" + input_ext
        output_file = "voice.mp3"

        with open(input_file, 'wb') as f:
            f.write(downloaded_file)

        convert_to_mp3(input_file, output_file)

        # Send file to Shazam API
        with open(output_file, 'rb') as f:
            files = {'file': f}
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": SHZ_HOST
            }
            response = requests.post("https://shazam.p.rapidapi.com/songs/detect", files=files, headers=headers)

        result = response.json()

        if 'track' in result:
            title = result['track']['title']
            subtitle = result['track']['subtitle']
            url = result['track']['url']
            bot.reply_to(message, f"✅ آهنگ شناسایی شد:\n🎵 {title} - {subtitle}\n🌐 {url}")
        else:
            bot.reply_to(message, "❌ متأسفم، Shazam نتونست این آهنگ رو شناسایی کنه.")

    except Exception as e:
        bot.reply_to(message, f"❌ مشکلی پیش اومد:\n{e}")

bot.infinity_polling()
