import os
import requests
import telebot
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def extract_youtube_link(song_link):
    try:
        # اطمینان از فرمت صحیح
        if not song_link.startswith("https://song.link/"):
            return None, None
        
        api_url = f"https://api.song.link/v1-alpha.1/links?url={song_link}&userCountry=IR"
        response = requests.get(api_url)
        data = response.json()

        youtube_url = data["linksByPlatform"].get("youtube", {}).get("url")
        title = data.get("entitiesByUniqueId", {}).get(
            data.get("entityUniqueId", ""), {}).get("title", "Unknown Title")
        return youtube_url, title
    except Exception as e:
        print(f"[extract_youtube_link] Error: {e}")
        return None, None

def download_mp3(youtube_url, title):
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
        'default_search': 'ytsearch1'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return filename
    except Exception as e:
        print(f"[download_mp3] Error: {e}")
        return None

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "سلام! لینک song.link/y/... رو بفرست تا فایل MP3 رو برات دانلود کنم 🎧")

@bot.message_handler(content_types=['text'])
def handle_song_link(message):
    text = message.text.strip()
    
    if not text.startswith("https://song.link/y/"):
        bot.reply_to(message, "لطفاً فقط لینک song.link/y/... بفرست 🙏")
        return

    msg = bot.reply_to(message, "🔎 در حال شناسایی لینک...")

    youtube_url, title = extract_youtube_link(text)
    if not youtube_url:
        bot.edit_message_text("❌ نتونستم لینک YouTube رو از song.link پیدا کنم.", msg.chat.id, msg.message_id)
        return

    bot.edit_message_text("⬇️ در حال دانلود از یوتیوب...", msg.chat.id, msg.message_id)
    filename = download_mp3(youtube_url, title)

    if not filename:
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود فایل پیش اومد.")
        return

    with open(filename, "rb") as audio:
        bot.send_audio(message.chat.id, audio, caption=f"{title} 🎵")

    os.remove(filename)

bot.infinity_polling()
