import os
import logging
import telebot
import yt_dlp
from youtubesearchpython import VideosSearch
import uuid
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in environment variables!")

bot = telebot.TeleBot(BOT_TOKEN)

# کش جستجو و متن آهنگ
search_cache = {}
lyrics_cache = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! 🎧 اسم خواننده یا آهنگ رو بفرست تا لیست آهنگ‌ها رو ببینی.")

@bot.message_handler(func=lambda message: True)
def handle_song_request(message):
    query = message.text.strip()
    if not query:
        bot.reply_to(message, "❌ لطفاً اسم آهنگ یا خواننده رو وارد کن.")
        return

    bot.send_message(message.chat.id, "🔍 در حال جستجو در یوتیوب...")

    try:
        search = VideosSearch(query, limit=10)
        results = search.result().get('result', [])
        if not results:
            bot.send_message(message.chat.id, "❌ آهنگی پیدا نشد.")
            return

        search_cache[str(message.chat.id)] = search

        markup = InlineKeyboardMarkup()
        for video in results:
            title = video['title']
            url = video['link']
            markup.add(InlineKeyboardButton(title[:40], callback_data=f"play|{url}"))

        markup.add(InlineKeyboardButton("🎵 آهنگ‌های بیشتر", callback_data="more"))
        bot.send_message(message.chat.id, "🎶 آهنگ مورد نظر رو انتخاب کن:", reply_markup=markup)

    except Exception as e:
        logging.exception("Search error")
        bot.send_message(message.chat.id, f"❌ خطا در جستجو: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == "more")
def handle_more_results(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in search_cache:
        bot.answer_callback_query(call.id, "⛔ جستجو پیدا نشد.")
        return

    search = search_cache[chat_id]
    try:
        search.next()
        results = search.result().get('result', [])
        markup = InlineKeyboardMarkup()

        for video in results:
            title = video['title']
            url = video['link']
            markup.add(InlineKeyboardButton(title[:40], callback_data=f"play|{url}"))

        markup.add(InlineKeyboardButton("🎵 آهنگ‌های بیشتر", callback_data="more"))
        bot.edit_message_text("🎶 ادامه آهنگ‌ها:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    except Exception as e:
        logging.exception("Pagination error")
        bot.answer_callback_query(call.id, "❌ خطا در دریافت ادامه آهنگ‌ها.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("play|"))
def download_selected_song(call):
    video_url = call.data.split("|")[1]
    msg = bot.send_message(call.message.chat.id, "⬇️ در حال دانلود MP3...")

    try:
        filename = f"{uuid.uuid4()}.%(ext)s"
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'outtmpl': f'{uuid.uuid4()}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            title = info_dict.get("title", "audio")
            ydl.download([video_url])

        mp3_file = filename.replace('%(ext)s', 'mp3')
        if not os.path.exists(mp3_file):
            bot.edit_message_text("❌ فایل پیدا نشد.", chat_id=call.message.chat.id, message_id=msg.message_id)
            return

        with open(mp3_file, 'rb') as f:
            bot.send_audio(
                call.message.chat.id,
                f,
                title=title,
                caption=f"{title}\n🎧 Powered by @mosicrobot"
            )

        unique_id = str(uuid.uuid4())
        lyrics_cache[unique_id] = title

        lyrics_markup = InlineKeyboardMarkup()
        lyrics_markup.add(InlineKeyboardButton("📃 متن آهنگ", callback_data=f"lyrics|{unique_id}"))
        bot.send_message(call.message.chat.id, "برای دیدن متن آهنگ روی دکمه زیر کلیک کن:", reply_markup=lyrics_markup)

        os.remove(mp3_file)
        bot.delete_message(call.message.chat.id, msg.message_id)

    except Exception as e:
        logging.exception("Download error")
        bot.edit_message_text(f"❌ خطا در دانلود: {str(e)}", chat_id=call.message.chat.id, message_id=msg.message_id)


# اجرای ربات
bot.infinity_polling()
