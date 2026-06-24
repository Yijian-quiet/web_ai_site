FROM python:3.11-slim

WORKDIR /app

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV HF_ENDPOINT=https://hf-mirror.com
RUN mkdir -p persona .streamlit

EXPOSE 8501
CMD ["streamlit", "run", "app_qwen.py", "--server.address=0.0.0.0", "--server.port=8501"]
