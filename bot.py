import os
import telebot
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SHZ_HOST = os.getenv("SHZ_HOST")

bot = telebot.TeleBot(BOT_TOKEN)

# ================= Shazam API =================
def recognize_song(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            "https://shazam.p.rapidapi.com/songs/v2/detect",
            headers={
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": SHZ_HOST,
                "Content-Type": "text/plain"
            },
            data=f.read()
        )
    if response.status_code == 200:
        json_data = response.json()
        try:
            title = json_data['track']['title']
            artist = json_data['track']['subtitle']
            return f"{artist} - {title}"
        except:
            return None
    return None

# ================= Melobit API =================
def search_melobit(track_name):
    query = track_name.replace(" ", "%20")
    url = f"https://www.melobit.com/api/v1/search/query/{query}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        if data.get("songs"):
            song = data["songs"][0]
            title = song["title"]
            artist = song["artists"][0]["fullName"]
            audio_url = song["audio"]["high"]["url"]
            return title, artist, audio_url
    return None, None, None

def send_full_track(chat_id, title, artist, audio_url):
    filename = f"{title}_{artist}.mp3"
    try:
        r = requests.get(audio_url, stream=True)
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        audio = open(filename, 'rb')
        bot.send_audio(chat_id, audio, title=title, performer=artist)
        audio.close()
        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در ارسال آهنگ: {e}")

# ================= Handlers =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎧 سلام! یک ویس یا ویدیو یا فایل آهنگ بفرست تا موزیک رو برات کامل بفرستم.")

@bot.message_handler(content_types=['audio', 'voice', 'video'])
def handle_audio(message):
    try:
        file_info = bot.get_file(message.audio.file_id if message.content_type == 'audio'
                                 else message.voice.file_id if message.content_type == 'voice'
                                 else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_name = "input_file.ogg" if message.content_type == 'voice' else "input_file.mp4"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.send_message(message.chat.id, "🎵 در حال شناسایی آهنگ...")

        track_name = recognize_song(file_name)
        if track_name:
            title, artist, audio_url = search_melobit(track_name)
            if audio_url:
                send_full_track(message.chat.id, title, artist, audio_url)
            else:
                bot.send_message(message.chat.id, f"آهنگ شناسایی شد ولی در Melobit پیدا نشد: {track_name}")
        else:
            bot.send_message(message.chat.id, "متاسفم، نتونستم آهنگ رو شناسایی کنم 😔")

        os.remove(file_name)

    except Exception as e:
        bot.send_message(message.chat.id, f"خطا در پردازش: {e}")

# ================= Start Bot =================
#bot.infinity_polling()
