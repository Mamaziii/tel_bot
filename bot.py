import os
import requests
import yt_dlp
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from io import BytesIO

# تنظیمات
TOKEN = os.environ.get("TOKEN")  # توکن ربات از متغیر محیطی
TEMP_DIR = "/tmp"  # مسیر موقت برای ذخیره فایل‌ها

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎵 سلام! لینک آهنگ از song.link یا یوتیوب را بفرستید تا فایل mp3 آن را برای شما ارسال کنم.")

def download_audio(url):
    """دانلود آهنگ از یوتیوب و تبدیل به mp3"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        return filename

def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    
    # بررسی آیا لینک song.link/y/ یا یوتیوب است
    if "song.link/y/" in user_input or "youtu.be/" in user_input:
        try:
            # استخراج ID ویدیو از لینک
            if "song.link/y/" in user_input:
                video_id = user_input.split("song.link/y/")[1].split("?")[0].split("&")[0]
            else:
                video_id = user_input.split("youtu.be/")[1].split("?")[0].split("&")[0]
            
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            update.message.reply_text("🔍 در حال پردازش آهنگ... لطفاً صبر کنید.")
            
            # دانلود آهنگ
            audio_path = download_audio(youtube_url)
            
            # ارسال فایل به کاربر
            with open(audio_path, 'rb') as audio_file:
                update.message.reply_audio(
                    audio=InputFile(audio_file),
                    caption="🎧 آهنگ شما آماده شد!"
                )
            
            # حذف فایل موقت
            os.remove(audio_path)
            
        except Exception as e:
            update.message.reply_text(f"خطا در پردازش آهنگ: {str(e)}")
    else:
        update.message.reply_text("لطفاً یک لینک معتبر از song.link/y/... یا youtu.be/... ارسال کنید.")

def main():
    # ساخت آپدیت کننده
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    # اضافه کردن هندلرها
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
