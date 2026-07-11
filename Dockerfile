FROM python:3.11-slim

# අවශ්‍ය පද්ධතිමය Dependencies ස්ථාපනය කිරීම
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# bot.py ගොනුව භාවිතා කිරීම වඩා සුදුසුය
CMD ["python", "bot.py"]
