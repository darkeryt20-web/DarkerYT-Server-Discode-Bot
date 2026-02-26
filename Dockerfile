FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ports EXPOSE කිරීම
EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003

# සියලුම scripts එකවර රන් කිරීම
# & පාවිච්චි කරන්නේ background එකේ රන් කිරීමටයි
CMD python verify.py & python welcome.py & python main.py & python web.py
