# Python 3.11 slim image එක පාවිච්චි කරනවා (Size එක අඩු නිසා වේගවත්)
FROM python:3.11-slim

# අවශ්‍ය System dependencies (Image processing සහ Discord voice/fonts සඳහා)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ඇප් එක තියෙන folder එක හදනවා
WORKDIR /app

# Requirements install කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# සියලුම ෆයිල්ස් ඇප් එක ඇතුළට කොපි කරනවා
COPY . .

# Dashboard එක පාවිච්චි කරන Port එක (අපි හදපු web.py එකේ port එක)
EXPOSE 8003

# පයිතන් scripts හතරම එකවර background එකේ run කරන විධානය
# මෙහිදී 'wait' මඟින් scripts ඔක්කොම එකවර ක්‍රියාත්මකව තබා ගනී
CMD python main.py & python verify.py & python welcome.py & python web.py && wait
