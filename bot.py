import os
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 یه ویس یا ویدیو بفرست تا با AudD شناسایی کنم!")

@bot.message_handler(content_types=['voice', 'audio', 'video'])
def handle_audio(message):
    try:
        file_info = bot.get_file(message.voice.file_id if message.voice else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_name = "voice.ogg" if message.voice else "video.mp4"
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)

        with open(file_name, 'rb') as f:
            files = {
                'file': f,
            }
            data = {
                'api_token': AUDD_API_TOKEN,
                'return': 'apple_music,spotify',
            }
            response = requests.post('https://api.audd.io/', data=data, files=files)

        result = response.json()
        if result.get("status") != "success" or not result.get("result"):
            bot.reply_to(message, "❌ AudD نتونست آهنگ رو شناسایی کنه.")
            return

        track = result['result']
        title = track.get("title", "نامشخص")
        artist = track.get("artist", "نامشخص")
        link = track.get("song_link", "لینک ناموجود")

        msg = f"✅ شناسایی شد:\n🎵 {title} - {artist}\n🔗 {link}"
        bot.reply_to(message, msg)

    except Exception as e:
        bot.reply_to(message, f"❌ خطایی رخ داد:\n{e}")

bot.infinity_polling()
