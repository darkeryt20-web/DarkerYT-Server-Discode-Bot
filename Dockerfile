FROM python:3.11-slim

# පද්ධතිමය අවශ්‍යතා ස්ථාපනය කිරීම
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements ස්ථාපනය කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# සියලුම කෝඩ් ගොනු copy කිරීම
COPY . .

# Verification.py ගොනුව ක්‍රියාත්මක කිරීම
CMD ["python", "Verification.py"]
