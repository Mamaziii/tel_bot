import os
import telebot
import asyncio
from shazamio import Shazam
from aiohttp import ClientConnectorError
from dotenv import load_dotenv

# بارگذاری مقادیر از .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# شروع ربات
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎧 سلام! ویس، فایل صوتی یا ویدیو بفرست تا اسم آهنگ رو برات پیدا کنم.")

# مدیریت فایل‌های صوتی، ویس یا ویدیو
@bot.message_handler(content_types=['audio', 'voice', 'video'])
def handle_audio(message):
    try:
        file_info = bot.get_file(message.audio.file_id if message.audio else message.voice.file_id if message.voice else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_name = "temp_audio.mp3"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        asyncio.run(recognize_song(message, file_name))
        os.remove(file_name)

    except Exception as e:
        bot.reply_to(message, f"⚠️ خطا در پردازش: {e}")

# شناسایی آهنگ با Shazam
async def recognize_song(message, file_path):
    shazam = Shazam()
    try:
        out = await shazam.recognize_song(file_path)
        if out.get("track"):
            title = out['track']['title']
            subtitle = out['track']['subtitle']
            link = out['track']['url']
            msg = f"🎵 {title} - {subtitle}\n🔗 {link}"
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "متاسفم، نتونستم آهنگ رو شناسایی کنم.")
    except ClientConnectorError:
        bot.send_message(message.chat.id, "❌ اتصال به Shazam ممکن نیست. لطفاً بعداً تلاش کنید.")

print("✅ Bot is running...")
bot.infinity_polling()
