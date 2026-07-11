FROM python:3.11-slim

# අවශ්‍ය System dependencies ස්ථාපනය කිරීම
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements install කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# සියලුම ෆයිල්ස් ඇප් එක ඇතුළට කොපි කරනවා
COPY . .

# Verification.py ක්‍රියාත්මක කිරීම
CMD ["python", "Verification.py"]
