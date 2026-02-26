FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dashboard Port
EXPOSE 8003

# Run all 4 scripts concurrently
CMD python main.py & python verify.py & python welcome.py & python web.py
