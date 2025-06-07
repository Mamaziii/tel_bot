import os
import telebot
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'extract_flat': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)
            if 'entries' in result and result['entries']:
                return result['entries'][0]['webpage_url']
    except Exception as e:
        print(f"Search error: {e}")
    return None

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
    bot.reply_to(message, "سلام! فقط اسم آهنگ یا خواننده رو بفرست تا از یوتیوب MP3 بگیرم 🎵")

@bot.message_handler(content_types=['text'])
def handle_query(message):
    query = message.text.strip()
    msg = bot.reply_to(message, "🔍 در حال جستجو در YouTube...")

    youtube_url = search_youtube(query)

    if not youtube_url:
        bot.edit_message_text("❌ هیچ آهنگی پیدا نشد.", msg.chat.id, msg.message_id)
        return

    bot.edit_message_text("⬇️ در حال دانلود MP3...", msg.chat.id, msg.message_id)
    filename = download_mp3_from_youtube(youtube_url, query)

    if not filename or not os.path.exists(filename):
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود فایل پیش آمد.")
        return

    with open(filename, "rb") as audio:
        bot.send_audio(message.chat.id, audio, caption=f"{query} 🎧")

    os.remove(filename)

bot.infinity_polling()
