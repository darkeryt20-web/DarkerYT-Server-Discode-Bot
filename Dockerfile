# Python 3.11 slim image එක පාවිච්චි කරනවා
FROM python:3.11-slim

# අවශ්‍ය System dependencies (Image processing, Discord voice, සහ PostgreSQL සඳහා)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    fonts-dejavu-core \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ඇප් එක තියෙන folder එක හදනවා
WORKDIR /app

# Requirements install කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# සියලුම ෆයිල්ස් ඇප් එක ඇතුළට කොපි කරනවා
COPY . .

# Dashboard එක පාවිච්චි කරන Port එක
EXPOSE 8003

# පයිතන් script එක run කිරීම
# අවවාදය: ඔබ bot.py සහ Verification.py යන දෙකම එකම කෝඩ් එකකින් සමන්විත වන පරිදි (Duplicate) උඩුගත කර ඇත.
# bot.py එකම පාවිච්චි කිරීම සුදුසුය.
CMD ["python", "bot.py"]
