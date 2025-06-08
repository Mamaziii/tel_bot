import os
import telebot
from youtubesearchpython import VideosSearch
import requests
from bs4 import BeautifulSoup

# 🔐 توکن ربات خودت رو اینجا بذار
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# 🎯 تابع جستجوی ویدیو در یوتیوب
def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    if result['result']:
        video_url = result['result'][0]['link']
        title = result['result'][0]['title']
        return video_url, title
    return None, None

# 🎵 تابع گرفتن لینک MP3 از سایت تبدیل‌کننده
def get_mp3_download_url(youtube_url):
    try:
        video_id = youtube_url.split("v=")[-1]
        api_url = f"https://api.vevioz.com/api/button/mp3/{video_id}"
        response = requests.get(api_url)
        soup = BeautifulSoup(response.text, "html.parser")
        a_tag = soup.find("a", class_="btn")
        if a_tag and "href" in a_tag.attrs:
            return a_tag["href"]
    except Exception as e:
        print("خطا در گرفتن لینک mp3:", e)
    return None

# 📩 هندل پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text.strip()
    msg = bot.reply_to(message, "🔎 در حال جستجو در یوتیوب...")

    youtube_url, title = search_youtube(query)
    if not youtube_url:
        bot.send_message(message.chat.id, "❌ ویدیویی پیدا نشد.")
        return

    bot.edit_message_text("⬇️ در حال دریافت فایل MP3...", chat_id=msg.chat.id, message_id=msg.message_id)

    mp3_url = get_mp3_download_url(youtube_url)
    if mp3_url:
        try:
            bot.send_audio(message.chat.id, audio=mp3_url, caption=f"🎵 {title}")
        except Exception as e:
            print("خطا در ارسال فایل:", e)
            bot.send_message(message.chat.id, "❌ مشکلی در ارسال فایل MP3 پیش اومد.")
    else:
        bot.send_message(message.chat.id, "❌ مشکلی در دانلود آهنگ پیش اومد.")

# 🚀 شروع ربات
if __name__ == "__main__":
    print("ربات با موفقیت اجرا شد.")
    bot.infinity_polling()
