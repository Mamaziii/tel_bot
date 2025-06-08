import os
import requests
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtubesearchpython import VideosSearch

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def search_youtube(query):
    videosSearch = VideosSearch(query, limit=1)
    result = videosSearch.result()
    try:
        url = result['result'][0]['link']
        title = result['result'][0]['title']
        return url, title
    except Exception as e:
        print("❌ YouTube search error:", e)
        return None, None


def download_mp3(youtube_url, title):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info_dict).replace(".webm", ".mp3").replace(".m4a", ".mp3")
        return filename
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def generate_songlink(youtube_url):
    try:
        api_url = f"https://api.song.link/v1-alpha.1/links?url={youtube_url}&userCountry=IR"
        response = requests.get(api_url)
        data = response.json()
        return data.get("pageUrl")
    except Exception as e:
        print(f"❌ Odesli (song.link) error: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! اسم آهنگ یا خواننده رو بفرست تا برات دانلودش کنم 🎧")

@bot.message_handler(content_types=['text'])
def on_text(message):
    import subprocess
    subprocess.run(["yt-dlp", "--extract-audio", "--audio-format", "mp3", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"], check=True)
    query = message.text.strip()
    msg = bot.reply_to(message, "🔎 در حال جستجو در یوتیوب...")

    youtube_url, title = search_youtube(query)
    if not youtube_url:
        bot.edit_message_text("❌ نتونستم تو یوتیوب چیزی پیدا کنم.", msg.chat.id, msg.message_id)
        return

    bot.edit_message_text("⬇️ در حال دانلود فایل MP3...", msg.chat.id, msg.message_id)
    filename = download_mp3(youtube_url, title)
    print(f"📎 YouTube URL: {youtube_url}")
    print(f"🎵 File name: {filename}")

    if not filename:
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود آهنگ پیش اومد.")
        return

    songlink_url = generate_songlink(youtube_url)

    keyboard = InlineKeyboardMarkup()
    if songlink_url:
        keyboard.add(InlineKeyboardButton("ℹ️ Info", url=songlink_url))

    with open(filename, "rb") as f:
        bot.send_audio(message.chat.id, f, caption=title, reply_markup=keyboard)

    os.remove(filename)

bot.infinity_polling()
