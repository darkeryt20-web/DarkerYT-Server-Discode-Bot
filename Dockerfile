FROM python:3.10-slim

# Install FFmpeg for the music system
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Koyeb Health Check Port
EXPOSE 8000

CMD ["python", "main.py"]
