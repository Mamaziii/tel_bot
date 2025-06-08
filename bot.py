import os
import logging
import re
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

logging.basicConfig(level=logging.DEBUG)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

### 🔎 جست‌وجو در song.link با استفاده از API رسمی
import urllib.parse

def search_youtube(query):
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if results:
            url_suffix = results[0]["url_suffix"]
            title = results[0]["title"]
            return f"https://www.youtube.com{url_suffix}", title
    except Exception as e:
        print(f"❌ YouTube search error: {e}")
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




### 🎵 دانلود MP3 از یوتیوب با yt-dlp
def download_mp3_from_youtube(youtube_url, title):
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
    filename = f"{safe_title}.mp3"
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return filename

### ⚙️ شروع و پردازش پیام‌ها
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg, "✨ سلام! اسمی از آهنگ یا خواننده بفرست تا برات لیست 5 آهنگ پیشنهادی بیارم.")

@bot.message_handler(func=lambda m: True)
def on_text(msg):
    query = msg.text.strip()
    arr = search_song_link(query)
    if not arr:
        bot.reply_to(msg, "❌ آهنگی پیدا نشد.")
        return
    
    kb = InlineKeyboardMarkup()
    for song in arr[:5]:
        kb.add(InlineKeyboardButton(
            text=f"{song['title']} – {song['artist']}",
            callback_data=f"DL|{song['id']}"
        ))
    bot.send_message(msg.chat.id, "لطفاً از بین آهنگ‌ها انتخاب کن:", reply_markup=kb)

@bot.callback_query_handler(lambda cb: cb.data.startswith("DL|"))
def on_select(cb):
    song_id = cb.data.split("|")[1]
    # مجدد درخواست برای اطلاعات کامل آهنگ
    data = requests.get(f"https://api.song.link/v1-alpha.1/links?userCountry=IR&entityUniqueId={song_id}").json()
    entity = data["entitiesByUniqueId"][song_id]
    yt_url = data["linksByPlatform"].get("youtube", {}).get("url")
    title = entity["title"] + " – " + entity["artistName"]
    info_url = data.get("pageUrl")

    bot.edit_message_text(chat_id=cb.message.chat.id, message_id=cb.message.message_id,
                          text=f"در حال دانلود {title}...")

    try:
        file = download_mp3_from_youtube(yt_url, title)
        kb = InlineKeyboardMarkup()
        if info_url:
            kb.add(InlineKeyboardButton(text="ℹ️ Info", url=info_url))
        with open(file, "rb") as f:
            bot.send_audio(cb.message.chat.id, f, caption=title, reply_markup=kb)
        os.remove(file)
    except Exception as e:
        bot.send_message(cb.message.chat.id, "❌ مشکلی در دانلود آهنگ پیش آمد.")

if __name__ == "__main__":
    bot.infinity_polling()
