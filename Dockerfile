# 1. Python base image එකක් තෝරා ගැනීම
FROM python:3.11-slim

# 2. FFmpeg ඇතුළු අවශ්‍ය system tools ඉන්ස්ටෝල් කිරීම
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 3. වැඩ කරන තැන (Working Directory) සකස් කිරීම
WORKDIR /app

# 4. Requirements ටික කොපි කරලා ඉන්ස්ටෝල් කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ඔයාගේ සියලුම Bot files කොපි කිරීම
COPY . .

# 6. බොට්ව Run කරන විධානය
CMD ["python", "main.py"]
