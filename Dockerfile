FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y gcc g++ ffmpeg

RUN pip install --upgrade pip

# تغییر این خط برای چاپ کامل ارورها
RUN pip install -r requirements.txt || (cat requirements.txt && echo "❌ pip install failed" && exit 1)

CMD ["python", "bot.py"]
