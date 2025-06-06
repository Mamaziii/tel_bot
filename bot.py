import os
import requests
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# تنظیمات
TOKEN = os.environ.get("TOKEN")  # توکن ربات از متغیر محیطی
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")  # کلید یوتیوب API

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 سلام! من ربات تشخیص آهنگ هستم. آهنگ را بفرستید یا نامش را جستجو کنید.")

def search_song(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    if not query:
        update.message.reply_text("لطفاً نام آهنگ را بنویسید. مثال: /search آهنگ جدید")
        return

    # جستجو در یوتیوب
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=1"
    response = requests.get(url).json()

    if response.get("items"):
        video_id = response["items"][0]["id"]["videoId"]
        youtube_link = f"https://youtu.be/{video_id}"
        update.message.reply_text(f"🎵 لینک یوتیوب:\n{youtube_link}")
    else:
        update.message.reply_text("آهنگ پیدا نشد! 😢")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("search", search_song, pass_args=True))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
