import os
import requests
import telebot
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

def search_odesli(query):
    try:
        url = f"https://api.song.link/v1-alpha.1/links?userCountry=IR&songName={query}"
        response = requests.get(url)
        data = response.json()

        youtube_link = data["linksByPlatform"].get("youtube", {}).get("url")
        title = data.get("entitiesByUniqueId", {}).get(
            data.get("entityUniqueId", ""), {}).get("title", query)
        return youtube_link, title
    except Exception as e:
        print(f"Odesli error: {e}")
        return None, None

def download_mp3_from_youtube(youtube_url, title):
    filename = f"{title}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return filename
    except Exception as e:
        print(f"Download error: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! فقط اسم آهنگ یا خواننده رو بفرست تا برات فایل MP3 رو بیارم 🎶")

@bot.message_handler(content_types=['text'])
def handle_query(message):
    query = message.text.strip()
    msg = bot.reply_to(message, "🔎 در حال جستجو...")

    youtube_url, title = search_odesli(query)

    if not youtube_url:
        bot.edit_message_text("❌ آهنگ پیدا نشد یا در سرویس YouTube نبود.", msg.chat.id, msg.message_id)
        return

    bot.edit_message_text("⬇️ در حال دانلود MP3 از YouTube...", msg.chat.id, msg.message_id)
    filename = download_mp3_from_youtube(youtube_url, title)

    if not filename:
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود فایل پیش آمد.")
        return

    with open(filename, "rb") as audio:
        bot.send_audio(message.chat.id, audio, caption=f"{title} 🎧")

    os.remove(filename)

bot.infinity_polling()
