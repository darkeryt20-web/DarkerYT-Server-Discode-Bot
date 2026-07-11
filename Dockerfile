FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# entrypoint.sh ගොනුවට ක්‍රියාත්මක වීමේ අවසරය දෙන්න
RUN chmod +x entrypoint.sh

# container එක ආරම්භයේදී entrypoint.sh ක්‍රියාත්මක කරන්න
CMD ["./entrypoint.sh"]
