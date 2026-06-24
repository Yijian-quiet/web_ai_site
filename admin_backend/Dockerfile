FROM python:3.11-slim

WORKDIR /app

RUN pip install waitress markdown --no-cache-dir flask pymysql bcrypt python-dotenv fastembed onnxruntime

COPY . .
ENV HF_ENDPOINT=https://hf-mirror.com

EXPOSE 5000
CMD ["python3", "app.py"]
