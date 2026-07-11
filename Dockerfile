FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# script එකට ක්‍රියාත්මක වීමේ අවසරය ලබා දෙන්න
RUN chmod +x entrypoint.sh

# container එක ආරම්භ වන විට script එක ක්‍රියාත්මක කරන්න
CMD ["./entrypoint.sh"]
