FROM python:3.11-slim

WORKDIR /app

# Requirements ස්ථාපනය කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# කේතය කොපි කිරීම
COPY . .

# Gunicorn හරහා Flask ඇප් එක ක්‍රියාත්මක කිරීම (Koyeb සඳහා සුදුසුම ක්‍රමය)
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} Verification:app"]
