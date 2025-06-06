import os
import requests
import telebot
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def search_odesli(query):
    try:
        api_url = f"https://youtube.com/results?search_query={query}"
        response = requests.get(api_url)
        data = response.json()

        youtube_url = data["linksByPlatform"].get("youtube", {}).get("url")
        title = data.get("entitiesByUniqueId", {}).get(data.get("entityUniqueId", ""), {}).get("title", query)

        return youtube_url, title
    except Exception as e:
        print(f"[ODESLI ERROR] {e}")
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
        print(f"[YT_DOWNLOAD ERROR] {e}")
        return None

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "سلام! فقط اسم آهنگ یا خواننده رو بفرست 🎶 تا فایل MP3 بگیری 🎧")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    query = message.text.strip()
    msg = bot.reply_to(message, "🔍 در حال جستجو در Odesli...")

    youtube_url, title = search_odesli(query)
    if not youtube_url:
        bot.edit_message_text("❌ آهنگی پیدا نشد.", msg.chat.id, msg.message_id)
        return

    bot.edit_message_text("⬇️ در حال دانلود از یوتیوب...", msg.chat.id, msg.message_id)
    filename = download_mp3_from_youtube(youtube_url, title)

    if not filename:
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود فایل پیش آمد.")
        return

    try:
        with open(filename, "rb") as audio:
            bot.send_audio(message.chat.id, audio, caption=f"{title} 🎧")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ارسال فایل شکست خورد. خطا: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

bot.infinity_polling()
