FROM python:3.10-slim

# نصب ابزارهای سیستمی لازم
RUN apt-get update && apt-get install -y ffmpeg

# تنظیم پوشه کاری
WORKDIR /app

# کپی پروژه به داخل کانتینر
COPY . .

# نصب پکیج‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# اجرای بات
CMD ["python", "bot.py"]
