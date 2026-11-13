FROM python:3.10-slim

WORKDIR /app

# requirements.txt සහ අනෙකුත් files copy කරනවාද බලන්න
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
