# Use a slim version of Python for a smaller image size
FROM python:3.11-slim

# Install system dependencies for Voice and Web
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose ports for both Flask health checks
EXPOSE 8000
EXPOSE 8001

# Start Bot 1 in the background and Bot 2 in the foreground
CMD python main.py & python verify.py
