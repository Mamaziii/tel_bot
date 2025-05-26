import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

bot = telebot.TeleBot(TOKEN)

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "سلام! ویس یا اسم آهنگ بفرست تا پیداش کنم 🎶")

# Step 1: Voice or Video Handler
@bot.message_handler(content_types=['voice', 'video'])
def handle_audio(message):
    file_info = bot.get_file(message.voice.file_id if message.voice else message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("sample.ogg", 'wb') as f:
        f.write(downloaded_file)

    # Convert to MP3 using ffmpeg (assume it's installed)
    os.system("ffmpeg -i sample.ogg voice.mp3 -y")

    with open("voice.mp3", 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post("https://shazam.p.rapidapi.com/songs/v2/detect", 
                                     headers=HEADERS, files=files)
            data = response.json()

            title = data['track']['title']
            artist = data['track']['subtitle']

            bot.send_message(message.chat.id, f"🎵 پیدا شد: {title} - {artist}\nدر حال جست‌وجوی فایل...")

            search_and_send_mp3(message.chat.id, f"{title} {artist}")

        except Exception as e:
            bot.send_message(message.chat.id, f"مشکلی در تماس با Shazam پیش اومد.\n{e}")

# Step 2: Search in MP3Juices API and send file

def search_and_send_mp3(chat_id, query):
    try:
        res = requests.get(f"https://api-mp3juices.yt/api/search.php?q={query}&page=1")
        results = res.json()

        if results and results.get("data"):
            audio_url = results['data'][0]['url']
            title = results['data'][0]['title']
            bot.send_audio(chat_id, audio=audio_url, caption=f"🎶 {title}")
        else:
            bot.send_message(chat_id, "آهنگ پیدا نشد ❌")
    except Exception as e:
        bot.send_message(chat_id, f"خطا در جست‌وجو یا ارسال فایل:\n{e}")

bot.infinity_polling()
